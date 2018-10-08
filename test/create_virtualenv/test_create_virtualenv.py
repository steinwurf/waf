#!/usr/bin/env python
# encoding: utf-8
import pytest


@pytest.mark.networktest
def test_create_virtualenv(testdirectory):
    testdirectory.copy_file('test/create_virtualenv/wscript')
    testdirectory.copy_file('build/waf')

    download_path = testdirectory.mkdir('download')

    testdirectory.run(
        'python waf configure --download_path {}'.format(download_path.path()))

    assert testdirectory.contains_dir('virtualenv-*')
    assert download_path.contains_dir('15.1.0')

    testdirectory.run('python waf build --download_path {}'.format(
        download_path.path()))

    assert testdirectory.contains_dir('virtualenv-*')

    testdirectory.run('python waf clean')
