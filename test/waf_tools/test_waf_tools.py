#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pytest


@pytest.mark.networktest
def test_waf_tools(testdirectory):
    root = testdirectory

    # Note: waf will call "git config --get remote.origin.url" in this folder,
    # so "git init" is required to test the default behavior (https resolver)
    root.run('git', 'init')

    root.copy_file('test/waf_tools/main.cpp')
    root.copy_file('test/waf_tools/resolve.json')
    root.copy_file('test/waf_tools/wscript')
    root.copy_file('build/waf')

    # First, configure without any options
    r = root.run('python', 'waf', 'configure')
    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')
    # The cxx_default mkspec should be selected
    assert r.stdout.match('*Using the mkspec*cxx_default*')

    r = root.run('python', 'waf', 'build')
    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = root.run('python', 'waf', '--run_tests')
    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')
    assert r.stdout.match('*REACHED END OF TEST PROGRAM*')
    assert r.stdout.match('*successful runs 1/1*')

    # Configure again with some extra options
    r = root.run('python', 'waf', 'configure', '--cxx_mkspec=cxx_default',
                 'msvs2012')

    assert r.returncode == 0
    assert r.stdout.match("*'configure' finished successfully*")
    # The cxx_default mkspec should be selected, and the output path should
    # be the same on all platforms
    output_path = os.path.join(root.path(), 'build', 'cxx_default')
    assert r.stdout.match('*Setting out to*{}*'.format(output_path))
    assert r.stdout.match('*Using the mkspec*cxx_default*')

    assert r.stdout.match("*'msvs2012' finished successfully*")
    assert r.stdout.match("*MAIN PROGRAM FOUND:*")
    assert r.stdout.match(
        "*<task_gen 'waf-tools-tester' declared in {}>*".format(root.path()))
    assert r.stdout.match('*OUTPUT PATH:*')

    # The Visual Studio solution and project files should be generated
    assert os.path.isfile(
        os.path.join(root.path(), 'waf-tools-tester_2012.sln'))
    assert os.path.isfile(
        os.path.join(root.path(), 'waf-tools-tester_2012.vcxproj'))

    # Build the test binary at the new location
    r = root.run('python', 'waf', 'build')
    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    # The executable should be found at the same location on all platforms
    program_name = 'waf-tools-tester'
    if sys.platform == 'win32':
        program_name += '.exe'
    program_path = os.path.join(output_path, program_name)

    assert os.path.isfile(program_path)

    r = root.run('python', 'waf', '--run_tests')
    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')
    assert r.stdout.match('*REACHED END OF TEST PROGRAM*')
    assert r.stdout.match('*successful runs 1/1*')

    # Now we install the executable using install_path and install_relative
    r = root.run('python', 'waf', 'install', '--install_path=inst',
                 '--install_relative')

    assert r.returncode == 0
    assert r.stdout.match("*'install' finished successfully*")
    # Make sure that the file was copied to the expected location
    output_path = os.path.join(root.path(), 'inst', 'build', 'cxx_default')
    program_path = os.path.join(output_path, program_name)

    assert os.path.isfile(program_path)
