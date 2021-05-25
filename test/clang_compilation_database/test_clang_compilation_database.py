#!/usr/bin/env python
# encoding: utf-8


def test_clang_compilation_database(testdirectory):
    testdirectory.copy_file("test/clang_compilation_database/main.cpp")
    testdirectory.copy_file("test/clang_compilation_database/wscript")
    testdirectory.copy_file("build/waf")

    testdirectory.run("python waf configure")
    testdirectory.run("python waf build")

    assert testdirectory.contains_file(filename="build/compile_commands.json")
