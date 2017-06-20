#!/usr/bin/env python
# encoding: utf-8

import pytest
from pytest_testdirectory.runresulterror import RunResultError


def test_fail_recurse(testdirectory):

    # @todo I guess this should fail since there is no wscript in or
    # anything in the foo folder

    foo_dir = testdirectory.mkdir('foo')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python', 'waf', 'configure',
                          '--foo_path={}'.format(foo_dir.path()))

    assert r.stdout.match('*finished successfully*')

    testdirectory.run('python', 'waf', 'build')


def test_fail_recurse_fail_configure(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    foo_dir.copy_file('test/fail_recurse/wscript_fail_configure',
                      rename_as='wscript')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    with pytest.raises(RunResultError):
        r = testdirectory.run('python', 'waf', 'configure',
                              '--foo_path={}'.format(foo_dir.path()))

    assert r.stderr.match('Recurse "foo" for "configure" failed.*')

    testdirectory.run('python', 'waf', 'build')
