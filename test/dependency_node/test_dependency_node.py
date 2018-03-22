#!/usr/bin/env python
# encoding: utf-8


def test_dependency_node(testdirectory):
    testdirectory.copy_file('test/dependency_node/fake_url_download.py')
    testdirectory.copy_file('test/dependency_node/wscript')
    testdirectory.copy_file('build/waf')

    testdirectory.run('python waf configure')
