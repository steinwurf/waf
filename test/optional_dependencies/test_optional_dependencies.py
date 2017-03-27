#!/usr/bin/env python
# encoding: utf-8

def test_optional_dependencies(test_directory):
    test_directory.copy_file('test/optional_dependencies/wscript')
    test_directory.copy_file('build/waf')

    test_directory.run('python', 'waf', 'configure')
    test_directory.run('python', 'waf', 'build')
