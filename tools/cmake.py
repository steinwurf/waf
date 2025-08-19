#! /usr/bin/env python
# encoding: utf-8

import os
import shutil
import sys
import waflib
import platform
import types
import tempfile
import multiprocessing
from pathlib import Path


def _limit_jobs_linux(default_jobs=1):
    """
    Calculate the number of jobs based on total system memory (Linux only).
    If unable to determine memory or not on Linux, return the default value.
    """
    if platform.system() != "Linux":
        # Not on Linux, return the default value
        return default_jobs

    meminfo_path = "/proc/meminfo"
    if not os.path.exists(meminfo_path):
        # /proc/meminfo not found, return the default value
        return default_jobs

    try:
        with open(meminfo_path, "r") as meminfo:
            for line in meminfo:
                if line.startswith("MemAvailable"):
                    # MemAvailable is memory a new application can use in kB
                    # without swapping MemTotal is in kB, convert to GB
                    total_memory_kb = int(line.split()[1])
                    total_memory_gb = total_memory_kb / (1024**2)
                    # Return jobs calculated as total_memory_gb / 2, minimum 1
                    return max(1, int(total_memory_gb / 2))
    except Exception as e:
        # Fallback to default if any error occurs
        print(f"Error reading memory info: {e}")
        return default_jobs


def _limit_jobs_generic(default_jobs=1):
    """
    Calculate the number of jobs based on available CPU cores (Windows only).
    Returns half the available cores, minimum 1. If not on Windows or error, returns default.
    """

    try:
        cores = multiprocessing.cpu_count()
        return max(1, int(cores / 2))
    except Exception as e:
        print(f"Error reading CPU core count: {e}")
        return default_jobs


def _limit_jobs(default_jobs=1):
    if platform.system() == "Linux":
        return _limit_jobs_linux(default_jobs)
    else:
        # For other platforms, return the default value
        return _limit_jobs_generic(default_jobs)


def options(ctx):

    ctx.add_option(
        "--cmake_build_type",
        default="Debug",
        help="CMake build type (Release, Debug, RelWithDebInfo, etc.)",
    )
    ctx.add_option("--cmake_toolchain", default="", help="Path to CMake toolchain file")

    ctx.add_option(
        "--cmake_verbose",
        action="store_true",
        default=False,
        help="Enable verbose output for CMake configure and build",
    )

    ctx.add_option(
        "--cmake_jobs",
        default=_limit_jobs(),
        help="Number of jobs for CMake build",
    )

    ctx.add_option(
        "--run_tests", action="store_true", default=False, help="Run tests after build"
    )

    # Make Ninja the default generator on Linux and Darwin, but allow it to be overridden
    if platform.system() == "Linux":
        default_generator = "Ninja"
    else:
        default_generator = ""

    ctx.add_option(
        "--cmake_generator",
        default=default_generator,
        help="CMake generator to use (e.g., Ninja, Unix Makefiles, etc.)",
    )

    ctx.add_option(
        "--ctest_valgrind",
        action="store_true",
        default=False,
        help="Run tests with Valgrind",
    )


def _cmake_configure(ctx, **kwargs):
    # Run the CMake configure command
    ctx.run_executable(ctx.env.CMAKE_CONFIGURE + ctx.env.CMAKE_CONFIGURE_ARGS, **kwargs)
    

def configure(ctx):
    # Add CMAKE_CONFIGURE_ARGS to the environment if it does not exist
    if not hasattr(ctx.env, "CMAKE_CONFIGURE_ARGS"):
        ctx.env.CMAKE_CONFIGURE_ARGS = []
    

    # set the default build optionas and flags, these can be overridden by the user in between load and configure
    if ctx.is_toplevel():
        if "CMAKE_BUILD_DIR" not in ctx.env:
            ctx.env.CMAKE_BUILD_DIR = ctx.path.get_bld().abspath()

        if "CMAKE_SRC_DIR" not in ctx.env:
            ctx.env.CMAKE_SRC_DIR = ctx.path.abspath()

    ctx.env.CMAKE_CONFIGURE = [
        "cmake",
        "-S",
        ctx.env.CMAKE_SRC_DIR,
        "-B",
        ctx.env.CMAKE_BUILD_DIR,
    ]

    ctx.env.CMAKE_BUILD_TYPE = ctx.options.cmake_build_type

    # Add the generator if specified
    if ctx.options.cmake_generator:
        ctx.env.CMAKE_CONFIGURE.append(f"-G{ctx.options.cmake_generator}")

    ctx.env.CMAKE_CONFIGURE_ARGS += [
        f"-DCMAKE_BUILD_TYPE={ctx.env.CMAKE_BUILD_TYPE}",
        # Make sure we don't resolve dependencies twice
        "-DSTEINWURF_RESOLVE=" + os.path.join(ctx.path.abspath(), "resolve_symlinks"),
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]

    if ctx.options.cmake_toolchain:
        # Expand ~, turn into absolute, resolve .. and symlinks
        toolchain_path = Path(ctx.options.cmake_toolchain).expanduser().resolve()

        # Check for existence
        if not toolchain_path.exists():
            ctx.fatal(f"CMAKE_TOOLCHAIN_FILE not found: {toolchain_path}")

        # Append the fully-normalized path
        ctx.env.CMAKE_CONFIGURE_ARGS.append(
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_path}"
        )

    if ctx.options.cmake_verbose:
        ctx.env.CMAKE_CONFIGURE_ARGS.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

    if not ctx.is_toplevel():
        return

    # Here we set up the environment for the CMake configure
    # The user can override this if needed. To run the conigure step call
    # use the cmake_configure function added to the configure context

    # Bind _cmake_configure as a method to ctx
    ctx.cmake_configure = types.MethodType(_cmake_configure, ctx)

    # Check if the CMake executable is available
    ctx.find_program("cmake", mandatory=True)


def _cmake_build(ctx, **kwargs):

    # Run the CMake build command
    ctx.run_executable(ctx.env.CMAKE_BUILD, **kwargs)

    if not ctx.options.run_tests:
        return

    ctx.run_executable(ctx.env.CMAKE_TEST_ARGS, **kwargs)


def build(ctx):

    # Add CMAKE_BUILD_ARGS to the environment if it does not exist
    if not hasattr(ctx.env, "CMAKE_TEST_ARGS"):
        ctx.env.CMAKE_TEST_ARGS = []
    
    # Run the tests using CTest
    # - How to use valgrind?
    # - gtest_filters?
    ctx.env.CMAKE_TEST_ARGS += [
        "ctest",
        "-VV",  # verbose output
        "--no-tests=error",
        "-C",
        ctx.env.CMAKE_BUILD_TYPE,
        "--test-dir",
        ctx.env.CMAKE_BUILD_DIR,
    ]

    if ctx.options.ctest_valgrind:
        valgrind = ctx.search_executable("valgrind")
        ctx.env.CMAKE_TEST_ARGS += [
            "--overwrite",
            f"MemoryCheckCommand={valgrind}",
            "--overwrite",
            "MemoryCheckCommandOptions=--error-exitcode=1 --tool=memcheck --leak-check=full",
            "-T",
            "memcheck",
        ]

    if not ctx.is_toplevel():
        return

    # Bind _cmake_build as a method to ctx
    ctx.cmake_build = types.MethodType(_cmake_build, ctx)

    jobs = str(ctx.options.cmake_jobs)
    cmake_build_cmd = [
        "cmake",
        "--build",
        ctx.env.CMAKE_BUILD_DIR,
        "--parallel",
        jobs,
    ]

    if ctx.options.cmake_verbose:
        cmake_build_cmd.append("--verbose")

    ctx.env.CMAKE_BUILD = cmake_build_cmd


class Clean(waflib.Context.Context):
    cmd = "clean"

    def execute(self):
        # If the main wscript has no "clean" function, bind it to an
        # empty function. This allows us to omit clean.
        if "clean" not in waflib.Context.g_module.__dict__:
            waflib.Context.g_module.clean = waflib.Utils.nada

        # Call the clean function in the top-level wscript
        super(Clean, self).execute()

        # Create a log file for the output
        log_path = os.path.join(tempfile.gettempdir(), "waf_clean.log")
        self.logger = waflib.Logs.make_logger(log_path, "cfg")

        paths = getattr(self, "clean_paths", ["build"])

        for path in paths:
            # If relative path, make it absolute
            if not os.path.isabs(path):
                path = os.path.join(self.path.abspath(), path)

            self.start_msg(f"Checking and removing {path}")
            if os.path.isdir(path):
                shutil.rmtree(path)
                self.end_msg("Removed")
            # Check for symlink
            elif os.path.islink(path):
                os.unlink(path)
                self.end_msg("Removed symlink")
            elif os.path.exists(path):
                os.remove(path)
                self.end_msg("Removed file")
            else:
                self.end_msg("Not found", color="YELLOW")
