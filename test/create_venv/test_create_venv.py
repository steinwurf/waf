#!/usr/bin/env python
# encoding: utf-8
import pytest
from pytest_testdirectory.runresulterror import RunResultError


@pytest.mark.networktest
def test_create_venv(testdirectory):
    testdirectory.copy_file("test/create_venv/wscript")
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")

    assert testdirectory.contains_dir("venv-*")

    testdirectory.run("python waf build")

    assert testdirectory.contains_dir("venv-*")

    testdirectory.run("python waf clean")


@pytest.mark.networktest
def test_create_venv_fail(testdirectory):
    """This test checks that if a user tries to create the venv
    in the build folder - we flag an error.
    """
    testdirectory.copy_file(
        "test/create_venv/wscript_build_folder", rename_as="wscript"
    )
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")

    assert testdirectory.contains_dir("venv-*")

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run("python waf build")

    r = excinfo.value.runresult

    assert r.stderr.match("Cannot create venv *")
