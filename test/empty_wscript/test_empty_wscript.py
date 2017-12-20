#!/usr/bin/env python
# encoding: utf-8


def test_empty_wscript(testdirectory):
    testdirectory.copy_file('test/empty_wscript/wscript')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python waf configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = testdirectory.run('python waf build')

    assert r.returncode == 0
