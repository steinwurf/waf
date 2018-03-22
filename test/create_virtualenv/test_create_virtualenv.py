#!/usr/bin/env python
# encoding: utf-8
import pytest


@pytest.mark.networktest
def test_create_virtualenv(testdirectory):
    testdirectory.copy_file('test/create_virtualenv/wscript')
    testdirectory.copy_file('build/waf')

    testdirectory.run('python waf configure')

    assert testdirectory.contains_dir('virtualenv-*')
