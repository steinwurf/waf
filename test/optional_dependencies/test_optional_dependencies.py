#!/usr/bin/env python
# encoding: utf-8

import pytest


@pytest.mark.networktest
def test_optional_dependencies(testdirectory):
    # @todo This test actually tries to use the network, which makes it slow!
    testdirectory.copy_file('test/optional_dependencies/wscript')
    testdirectory.copy_file('build/waf')

    testdirectory.run('python waf configure')
    testdirectory.run('python waf build')
