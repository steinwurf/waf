#!/usr/bin/env python
# encoding: utf-8
import pytest
from pytest_testdirectory.runresulterror import RunResultError


@pytest.mark.networktest
def test_create_virtualenv(testdirectory):
    testdirectory.copy_file("test/create_virtualenv/wscript")
    testdirectory.copy_file("build/waf")

    download_path = testdirectory.mkdir("download")

    testdirectory.run(
        "python waf configure --download_path {}".format(download_path.path())
    )

    assert testdirectory.contains_dir("virtualenv-*")
    assert download_path.contains_dir("16.4.3")

    testdirectory.run(
        "python waf build --download_path {}".format(download_path.path())
    )

    assert testdirectory.contains_dir("virtualenv-*")

    testdirectory.run("python waf clean")


@pytest.mark.networktest
def test_create_virtualenv_fail(testdirectory):
    """ This test checks that if a user tries to create the virtualenv
        in the build folder - we flag an error.
    """
    testdirectory.copy_file(
        "test/create_virtualenv/wscript_build_folder", rename_as="wscript"
    )
    testdirectory.copy_file("build/waf")

    download_path = testdirectory.mkdir("download")

    testdirectory.run(
        "python waf configure --download_path {}".format(download_path.path())
    )

    assert testdirectory.contains_dir("virtualenv-*")
    assert download_path.contains_dir("16.4.3")

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run(
            "python waf build --download_path {}".format(download_path.path())
        )

    r = excinfo.value.runresult

    assert r.stderr.match("Cannot create virtualenv *")
