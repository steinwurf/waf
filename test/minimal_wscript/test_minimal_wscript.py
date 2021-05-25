#!/usr/bin/env python
# encoding: utf-8


def test_minimal_wscript(testdirectory):
    testdirectory.copy_file("test/minimal_wscript/wscript")
    testdirectory.copy_file("build/waf")

    # The wscript has no "configure" function, but this step should not fail
    r = testdirectory.run("python waf configure")

    assert r.returncode == 0
    assert r.stdout.match("*finished successfully*")

    r = testdirectory.run("python waf build")

    assert r.returncode == 0
