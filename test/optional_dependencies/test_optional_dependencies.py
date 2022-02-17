#!/usr/bin/env python
# encoding: utf-8


def test_optional_dependencies(testdirectory):
    # @todo This test actually tries to use the network, which makes it slow!
    testdirectory.copy_file("test/optional_dependencies/wscript")
    testdirectory.copy_file("build/waf")
    testdirectory.copy_file("test/fake_git.py")

    testdirectory.run("python waf configure --resolve_path resolve_dependencies")
    testdirectory.run("python waf build")
