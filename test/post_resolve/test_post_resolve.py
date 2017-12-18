#!/usr/bin/env python
# encoding: utf-8


def test_post_resolve_run_http(testdirectory):
    testdirectory.copy_file('test/post_resolve/fake_url_download.py')
    testdirectory.copy_file('test/post_resolve/wscript')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python', 'waf', 'configure')

    assert r.stdout.match('*finished successfully*')

    assert testdirectory.contains_file(
        'resolved_dependencies/baz-*/run-*/somefile.txt')

    assert testdirectory.contains_file(
        'resolved_dependencies/baz-*/run-*/ok.txt')

    r = testdirectory.run('python', 'waf', 'build')

    assert r.returncode == 0
