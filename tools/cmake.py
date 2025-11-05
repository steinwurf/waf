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
import waflib.Utils
from pathlib import Path


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
        default=None,
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

    # Combine the base configure command with any additional arguments
    command = " ".join(ctx.env.CMAKE_CONFIGURE + ctx.env.CMAKE_CONFIGURE_ARGS)

    # Substitute variables in the command list
    command = waflib.Utils.subst_vars(command, ctx.env)

    # Run the CMake configure command
    ctx.run_executable(command, **kwargs)


def configure(ctx):

    if not ctx.is_toplevel():
        # Only run configure in the top-level wscript
        return

    # Add CMAKE_CONFIGURE_ARGS to the environment if it does not exist
    if not hasattr(ctx.env, "CMAKE_CONFIGURE_ARGS"):
        ctx.env.CMAKE_CONFIGURE_ARGS = []

    # set the default build optionas and flags, these can be overridden by the user in between load and configure

    if "CMAKE_BUILD_DIR" not in ctx.env:
        ctx.env.CMAKE_BUILD_DIR = ctx.path.get_bld().abspath()

    if "CMAKE_SRC_DIR" not in ctx.env:
        ctx.env.CMAKE_SRC_DIR = ctx.path.abspath()

    ctx.env.CMAKE_CONFIGURE = [
        "cmake",
        "-S",
        "${CMAKE_SRC_DIR}",
        "-B",
        "${CMAKE_BUILD_DIR}",
    ]

    ctx.env.CMAKE_BUILD_TYPE = ctx.options.cmake_build_type

    # Add the generator if specified
    if ctx.options.cmake_generator:
        ctx.env.CMAKE_CONFIGURE_ARGS.append(f"-G{ctx.options.cmake_generator}")

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
        ctx.env.CMAKE_CONFIGURE_ARGS.append(f"-DCMAKE_TOOLCHAIN_FILE={toolchain_path}")

    if ctx.options.cmake_verbose:
        ctx.env.CMAKE_CONFIGURE_ARGS.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

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

    if not ctx.is_toplevel():
        # Only run build in the top-level wscript
        return

    # Add CMAKE_BUILD_ARGS to the environment if it does not exist
    if not hasattr(ctx.env, "CMAKE_TEST_ARGS"):
        ctx.env.CMAKE_TEST_ARGS = []

    # Run the tests using CTest
    # - How to use valgrind?
    # - gtest_filters?
    ctx.env.CMAKE_TEST_ARGS += [
        "ctest",
        "-VV",  # verbose output
        "--output-on-failure",
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

    # Bind _cmake_build as a method to ctx
    ctx.cmake_build = types.MethodType(_cmake_build, ctx)

    cmake_build_cmd = [
        "cmake",
        "--build",
        ctx.env.CMAKE_BUILD_DIR,
    ]

    # Add flags to parallelize the build (these are different on windows)
    # When using Ninja, let it handle parallelization automatically (except on Windows)
    if platform.system() == "Windows":
        # Parallelize MSBuild https://devblogs.microsoft.com/cppblog/improved-parallelism-in-msbuild/
        cmake_build_cmd.append("--parallel")
        cmake_build_cmd.append("--")
        cmake_build_cmd.append("/p:UseMultiToolTask=true")
        cmake_build_cmd.append("/p:EnforceProcessCountAcrossBuilds=true")
    else:
        # Non-Windows platforms
        if ctx.options.cmake_jobs:
            jobs = str(ctx.options.cmake_jobs)
            cmake_build_cmd.extend(["--parallel", jobs])

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
