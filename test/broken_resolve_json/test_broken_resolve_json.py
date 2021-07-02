#!/usr/bin/env python
# encoding: utf-8

import pytest
from pytest_testdirectory.runresulterror import RunResultError


def test_broken_resolve_json(testdirectory):
    testdirectory.copy_file("test/broken_resolve_json/wscript")
    testdirectory.copy_file("test/broken_resolve_json/resolve.json")
    testdirectory.copy_file("build/waf")

    with pytest.raises(RunResultError) as excinfo:
        testdirectory.run("python waf configure")

    r = excinfo.value.runresult

    assert r.returncode != 0
    assert r.stderr.match("Error in load dependencies (resolve.json)*")
