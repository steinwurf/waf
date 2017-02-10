#!/usr/bin/env python
# encoding: utf-8


def test_empty_wscript(test_directory):
    test_directory.copy_files('test/empty_wscript/*')
    test_directory.copy_file('build/waf')

    print(test_directory.path())

    r = test_directory.run('python', 'waf', 'configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0
