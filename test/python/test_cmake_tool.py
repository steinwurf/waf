#!/usr/bin/env python
# encoding: utf-8

import pytest
import sys
import os
import types
import platform

# Mock waflib module to avoid import errors
class MockWaflib:
    class Context:
        class Context:
            pass
    class Utils:
        @staticmethod
        def nada():
            pass
    class Logs:
        @staticmethod
        def make_logger(path, name):
            pass

sys.modules['waflib'] = MockWaflib()
sys.modules['waflib.Context'] = MockWaflib.Context
sys.modules['waflib.Utils'] = MockWaflib.Utils  
sys.modules['waflib.Logs'] = MockWaflib.Logs

# Add the tools directory to the path so we can import cmake
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools'))

import cmake


class MockOptions:
    """Mock options object for testing cmake tool."""
    def __init__(self, cmake_generator="", cmake_jobs=4, cmake_verbose=False):
        self.cmake_generator = cmake_generator
        self.cmake_jobs = cmake_jobs
        self.cmake_verbose = cmake_verbose
        self.ctest_valgrind = False


class MockEnv:
    """Mock environment object for testing cmake tool."""
    def __init__(self):
        self.CMAKE_BUILD_DIR = "/tmp/build"
        self.CMAKE_BUILD_TYPE = "Debug"


class MockContext:
    """Mock context object for testing cmake tool."""
    def __init__(self, cmake_generator="", cmake_jobs=4):
        self.options = MockOptions(cmake_generator, cmake_jobs)
        self.env = MockEnv()
        
    def is_toplevel(self):
        return True
        
    def search_executable(self, name):
        """Mock search_executable method."""
        return f"/usr/bin/{name}"


def test_cmake_build_ninja_no_parallel():
    """Test that when Ninja generator is used, no --parallel flags are added."""
    ctx = MockContext(cmake_generator="Ninja")
    
    # Call the build function
    cmake.build(ctx)
    
    # Check that CMAKE_BUILD is set correctly
    assert hasattr(ctx.env, "CMAKE_BUILD")
    build_cmd = ctx.env.CMAKE_BUILD
    
    # Should contain basic cmake build command
    assert "cmake" in build_cmd
    assert "--build" in build_cmd
    assert ctx.env.CMAKE_BUILD_DIR in build_cmd
    
    # Should NOT contain --parallel flag when using Ninja
    assert "--parallel" not in build_cmd


def test_cmake_build_unix_makefiles_with_parallel():
    """Test that when Unix Makefiles generator is used, --parallel flags are added."""
    ctx = MockContext(cmake_generator="Unix Makefiles", cmake_jobs=8)
    
    # Call the build function
    cmake.build(ctx)
    
    # Check that CMAKE_BUILD is set correctly
    assert hasattr(ctx.env, "CMAKE_BUILD")
    build_cmd = ctx.env.CMAKE_BUILD
    
    # Should contain basic cmake build command
    assert "cmake" in build_cmd
    assert "--build" in build_cmd
    assert ctx.env.CMAKE_BUILD_DIR in build_cmd
    
    # Should contain --parallel flag when NOT using Ninja
    assert "--parallel" in build_cmd
    assert "8" in build_cmd


def test_cmake_build_no_generator_with_parallel():
    """Test that when no generator is specified, --parallel flags are added."""
    ctx = MockContext(cmake_generator="")
    
    # Call the build function
    cmake.build(ctx)
    
    # Check that CMAKE_BUILD is set correctly
    assert hasattr(ctx.env, "CMAKE_BUILD")
    build_cmd = ctx.env.CMAKE_BUILD
    
    # Should contain basic cmake build command
    assert "cmake" in build_cmd
    assert "--build" in build_cmd
    assert ctx.env.CMAKE_BUILD_DIR in build_cmd
    
    # Should contain --parallel flag when NOT using Ninja (empty string != "Ninja")
    assert "--parallel" in build_cmd


def test_cmake_build_ninja_case_sensitive():
    """Test that the Ninja check is case sensitive."""
    ctx = MockContext(cmake_generator="ninja")  # lowercase
    
    # Call the build function
    cmake.build(ctx)
    
    # Check that CMAKE_BUILD is set correctly
    assert hasattr(ctx.env, "CMAKE_BUILD")
    build_cmd = ctx.env.CMAKE_BUILD
    
    # Should contain --parallel flag when using lowercase "ninja" (not exactly "Ninja")
    assert "--parallel" in build_cmd