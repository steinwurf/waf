#!/usr/bin/env python
# encoding: utf-8


def test_post_resolve_run_http(testdirectory):
    testdirectory.copy_file('test/post_resolve/fake_url_download.py')
    testdirectory.copy_file('test/post_resolve/wscript')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python', 'waf', 'configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = testdirectory.run('python', 'waf', 'build')

    assert r.returncode == 0
