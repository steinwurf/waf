#!/usr/bin/env python
# encoding: utf-8

# @todo This is actually a test that uses network, which makes it slow.


def test_optional_dependencies(testdirectory):
    testdirectory.copy_file('test/optional_dependencies/wscript')
    testdirectory.copy_file('build/waf')

    testdirectory.run('python waf configure')
    testdirectory.run('python waf build')
