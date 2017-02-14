#!/usr/bin/env python
# encoding: utf-8

import os

def test_self_build(test_directory):

    src_dir = test_directory.mkdir('src')
    src_dir.copy_dir(directory='src/wurf')

    test_directory.copy_file('wscript')
    test_directory.copy_file('build/waf')

    r = test_directory.run('python', 'waf', 'configure', '--skip_tests')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0

    waf_path = os.path.join(test_directory.path(), 'build', 'waf')

    assert os.path.isfile(waf_path)
