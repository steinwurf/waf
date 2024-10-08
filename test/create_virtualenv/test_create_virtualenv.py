#!/usr/bin/env python
# encoding: utf-8
import pytest
from pytest_testdirectory.runresulterror import RunResultError

import platform


def test_create_virtualenv(testdirectory):
    # do not run on windows
    if platform.system() == "Windows":
        pytest.skip("Skipping test on Windows")
    testdirectory.copy_file("test/create_virtualenv/wscript")
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")
    testdirectory.run("python waf build ")

    assert testdirectory.contains_dir("virtualenv-*")

    testdirectory.run("python waf clean")


def test_create_virtualenv_fail(testdirectory):
    """This test checks that if a user tries to create the virtualenv
    in the build folder - we flag an error.
    """
    testdirectory.copy_file(
        "test/create_virtualenv/wscript_build_folder", rename_as="wscript"
    )
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure ")

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run("python waf build")

    r = excinfo.value.runresult

    assert not testdirectory.contains_dir("virtualenv-*")

    assert r.stderr.match("Cannot create virtualenv *")
