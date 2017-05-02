#!/usr/bin/env python
# encoding: utf-8

import os
import json
import pytest

def mkdir_app(directory):
    app_dir = directory.mkdir('app')
    app_dir.copy_file('test/http_dependency/app/main.cpp')
    app_dir.copy_file('test/http_dependency/app/wscript')

    app_dir.copy_file('build/waf')

    return app_dir

@pytest.mark.networktest
def test_http_dependency(test_directory):

    app_dir = mkdir_app(directory=test_directory)

    app_dir.run('python', 'waf', 'configure')
    app_dir.run('python', 'waf', 'build')
