#! /usr/bin/env python
# encoding: utf-8

import os
import shutil
import sys
import waflib
import platform
import types


def _limit_jobs_based_on_memory(default_jobs=1):
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


def options(ctx):

    ctx.add_option(
        "--cmake-build-type",
        default="Release",
        help="CMake build type (Release, Debug, RelWithDebInfo, etc.)",
    )
    ctx.add_option("--cmake-toolchain", default="", help="Path to CMake toolchain file")

    ctx.add_option(
        "--cmake-verbose",
        action="store_true",
        default=False,
        help="Enable verbose output for CMake configure and build",
    )

    ctx.add_option(
        "--cmake-jobs",
        default=_limit_jobs_based_on_memory(),
        help="Number of jobs for CMake build",
    )

    ctx.add_option(
        "--run-tests", action="store_true", default=False, help="Run tests after build"
    )


def _cmake_configure(ctx):

    # Run the CMake configure command
    ctx.run_command(ctx.env.CMAKE_CONFIGURE, stdout=None, stderr=None)


def configure(ctx):
    if not ctx.is_toplevel():
        return

    # Here we set up the environment for the CMake configure
    # The user can override this if needed. To run the conigure step call
    # use the cmake_configure function added to the configure context

    # Bind _cmake_configure as a method to ctx
    ctx.cmake_configure = types.MethodType(_cmake_configure, ctx)

    # Check if the CMake executable is available
    ctx.find_program("cmake", mandatory=True)

    ctx.env.BUILD_DIR = ctx.path.get_bld().abspath()

    cmake_cmd = [
        "cmake",
        "-S",
        ctx.path.abspath(),
        "-B",
        ctx.env.BUILD_DIR,
        f"-DCMAKE_BUILD_TYPE={ctx.options.cmake_build_type}",
        "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        # Make sure we don't resolve dependencies twice
        "-DSTEINWURF_RESOLVE=" + os.path.join(ctx.path.abspath(), "resolve_symlinks"),
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]

    if ctx.options.cmake_toolchain:
        cmake_cmd.append(f"-DCMAKE_TOOLCHAIN_FILE={ctx.options.cmake_toolchain}")

    if ctx.options.cmake_verbose:
        cmake_cmd.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

    ctx.env.CMAKE_CONFIGURE = cmake_cmd


def _cmake_build(ctx):

    # Run the CMake build command
    ctx.run_command(ctx.env.CMAKE_BUILD, stdout=None, stderr=None)

    if ctx.options.run_tests:

        # Run the tests using CTest
        ctest_cmd = [
            "ctest",
            "--test-dir",
            ctx.env.BUILD_DIR,
        ]

        if not ctx.options.cmake_verbose:
            ctest_cmd.append("--output-on-failure")

        ctx.run_command(ctest_cmd, stdout=None, stderr=None)


def build(ctx):

    if not ctx.is_toplevel():
        return

    # Bind _cmake_build as a method to ctx
    ctx.cmake_build = types.MethodType(_cmake_build, ctx)

    jobs = str(ctx.options.cmake_jobs)
    cmake_build_cmd = [
        "cmake",
        "--build",
        ctx.env.BUILD_DIR,
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
        self.logger = waflib.Logs.make_logger("/tmp/waf_clean.log", "cfg")

        paths = getattr(self, "clean_paths", ["build", "build_current"])

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
            else:
                self.end_msg("Not found", color="YELLOW")
