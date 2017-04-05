#!/usr/bin/env python
# encoding: utf-8

def test_minimal_wscript(test_directory):
    test_directory.copy_file('test/existing_tag/wscript')
    test_directory.copy_file('build/waf')

    # The wscript has no "configure" function, but this step should not fail
    r = test_directory.run('python', 'waf', 'configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0
