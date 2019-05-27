#!/usr/bin/env python
# encoding: utf-8


from wurf.rewrite import rewrite


def test_rewrite(testdirectory):
    wscript = testdirectory.copy_file(
        filename="test/add_dependency/app/wscript")

    with rewrite(filename=wscript) as f:

        pattern = r"VERSION = '\d+\.\d+\.\d+'"
        replacement = r"VERSION = '2.0.0'"

        f.regex_replace(pattern=pattern, replacement=replacement)
