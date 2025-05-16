#! /usr/bin/env python
# encoding: utf-8

import os
import shutil
import sys
import waflib


class CMake:

    def __init__(self, ctx):
        self.ctx = ctx

    def configure(self):
        # Check if the CMake executable is available
        self.ctx.find_program("cmake", mandatory=True)

        self.ctx.env.BUILD_DIR = self.ctx.path.get_bld().abspath()

        if not self.ctx.is_toplevel():
            return

        cmake_cmd = [
            "cmake",
            "-S",
            self.ctx.path.abspath(),
            "-B",
            self.ctx.env.BUILD_DIR,
            f"-DCMAKE_BUILD_TYPE={self.ctx.options.cmake_build_type}",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            # Make sure we don't resolve dependencies twice
            "-DSTEINWURF_RESOLVE="
            + os.path.join(self.ctx.path.abspath(), "resolve_symlinks"),
        ]

        # Add any additional CMake flags specified by the user in the CMAKE_ARGS
        if self.ctx.env.CMAKE_ARGS:
            cmake_cmd.extend(self.ctx.env.CMAKE_ARGS)

        if self.ctx.options.cmake_toolchain:
            cmake_cmd.append(
                f"-DCMAKE_TOOLCHAIN_FILE={self.ctx.options.cmake_toolchain}"
            )

        if self.ctx.options.cmake_verbose:
            cmake_cmd.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

        self.ctx.run_command(cmake_cmd, stdout=None, stderr=None)

    def build(self):

        if not self.ctx.is_toplevel():
            return

        jobs = str(self.ctx.options.jobs) if hasattr(self.ctx.options, "jobs") else "1"
        cmake_build_cmd = [
            "cmake",
            "--build",
            self.ctx.env.BUILD_DIR,
            "--parallel",
            jobs,
        ]

        if self.ctx.options.cmake_verbose:
            cmake_build_cmd.append("--verbose")

        self.ctx.run_command(cmake_build_cmd, stdout=None, stderr=None)

        if self.ctx.options.run_tests:

            # Run the tests using CTest
            ctest_cmd = [
                "ctest",
                "--test-dir",
                self.ctx.env.BUILD_DIR,
            ]

            if not self.ctx.options.cmake_verbose:
                ctest_cmd.append("--output-on-failure")

            self.ctx.run_command(ctest_cmd, stdout=None, stderr=None)


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
        "--run-tests", action="store_true", default=False, help="Run tests after build"
    )


def _cmake_configure(ctx):

    # Run the CMake configure command
    ctx.run_command(ctx.env.CMAKE_CONFIGURE, stdout=None, stderr=None)


def configure(ctx):
    # Here we set up the environment for the CMake configure
    # The user can override this if needed. To run the conigure step call
    # use the cmake_configure function added to the configure context
    setattr(ctx, "cmake_configure", _cmake_configure)

    # Check if the CMake executable is available
    ctx.find_program("cmake", mandatory=True)

    ctx.env.BUILD_DIR = ctx.path.get_bld().abspath()

    if not ctx.is_toplevel():
        return

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
    ]

    if ctx.options.cmake_toolchain:
        cmake_cmd.append(f"-DCMAKE_TOOLCHAIN_FILE={ctx.options.cmake_toolchain}")

    if ctx.options.cmake_verbose:
        cmake_cmd.append("-DCMAKE_VERBOSE_MAKEFILE=ON")

    ctx.env.CMAKE_CONFIGURE = cmake_cmd


def build(ctx):

    if not ctx.is_toplevel():
        return

    jobs = str(ctx.options.jobs) if hasattr(ctx.options, "jobs") else "1"
    cmake_build_cmd = [
        "cmake",
        "--build",
        ctx.env.BUILD_DIR,
        "--parallel",
        jobs,
    ]

    if ctx.options.cmake_verbose:
        cmake_build_cmd.append("--verbose")

    ctx.run_command(cmake_build_cmd, stdout=None, stderr=None)

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

        paths = getattr(self, "clean_paths", [])
        if not paths:
            self.fatal("No paths to clean")

        for path in paths:

            # If relative path, make it absolute
            if not os.path.isabs(path):
                path = os.path.join(self.path.abspath(), path)

            self.start_msg(f"Checking and removing {path}")
            if os.path.isdir(path):
                shutil.rmtree(path)
                self.end_msg("Removed")
            else:
                self.end_msg("Not found", color="YELLOW")
