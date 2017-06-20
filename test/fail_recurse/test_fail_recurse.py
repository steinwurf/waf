#!/usr/bin/env python
# encoding: utf-8


def test_fail_recurse(testdirectory):

    foo_dir = testdirectory.mkdir('foo')

    testdirectory.copy_file('test/fail_recurse/wscript')
    # testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python', 'waf', 'configure',
        '--foo_path={}'.format(foo_dir.path()))

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = testdirectory.run('python', 'waf', 'build')

    assert r.returncode == 0
