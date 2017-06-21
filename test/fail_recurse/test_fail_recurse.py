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


def test_fail_recurse_configure_python_error(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    foo_dir.copy_file('test/fail_recurse/wscript_configure_python_error',
                      rename_as='wscript')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run('python', 'waf', 'configure',
                          '--foo_path={}'.format(foo_dir.path()))

    r = excinfo.value.runresult

    assert r.stdout.match('RuntimeError: Oh no!')


def test_fail_recurse_build_python_error(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    foo_dir.copy_file('test/fail_recurse/wscript_build_python_error',
                      rename_as='wscript')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    r = testdirectory.run('python', 'waf', 'configure',
                          '--foo_path={}'.format(foo_dir.path()))

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run('python', 'waf', 'build')

    r = excinfo.value.runresult

    assert r.stdout.match('RuntimeError: Oh no!')


def test_fail_recurse_configure_waf_error(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    foo_dir.copy_file('test/fail_recurse/wscript_configure_waf_error',
                      rename_as='wscript')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run('python', 'waf', 'configure',
                          '--foo_path={}'.format(foo_dir.path()))

    r = excinfo.value.runresult

    assert r.stderr.match('Recurse "foo" for "configure" failed *')
    assert r.stderr.match('(complete log in *)')


def test_fail_recurse_build_waf_error(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    foo_dir.copy_file('test/fail_recurse/wscript_build_waf_error',
                      rename_as='wscript')

    testdirectory.copy_file('test/fail_recurse/wscript')
    testdirectory.copy_file('test/fail_recurse/resolve.json')
    testdirectory.copy_file('build/waf')

    testdirectory.run('python', 'waf', 'configure',
                      '--foo_path={}'.format(foo_dir.path()))

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run('python', 'waf', 'build')

    r = excinfo.value.runresult

    assert r.stderr.match('Recurse "foo" for "build" failed *')
    assert r.stderr.match('*(run with -v for more information)')
