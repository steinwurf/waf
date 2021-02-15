#!/usr/bin/env python
# encoding: utf-8

import pytest

from pytest_testdirectory.runresulterror import RunResultError


def test_internal_dependency(testdirectory):
    testdirectory.copy_file('test/internal_dependency/wscript')
    testdirectory.copy_file('build/waf')

    # Configure should fail since the specified dependency is invalid.
    with pytest.raises(RunResultError):
        testdirectory.run('python waf configure')

    # This should not since the dependency should be skipped
    testdirectory.run('python waf configure --skip_internal')
