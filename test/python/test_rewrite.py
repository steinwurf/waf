#!/usr/bin/env python
# encoding: utf-8

import pytest
from wurf.rewrite import rewrite_file


data = u"""
Here is some data. And there is also
a version number:
VERSION = '1.0.0'
hello hello
"""

expected = u"""
Here is some data. And there is also
a version number:
VERSION = '2.0.0'
hello hello
"""


def test_rewrite(testdirectory):
    filename = testdirectory.write_text(
        filename="test.txt", data=data, encoding="utf-8")

    with rewrite_file(filename=filename) as f:

        pattern = r"VERSION = '\d+\.\d+\.\d+'"
        replacement = r"VERSION = '2.0.0'"

        f.regex_replace(pattern=pattern, replacement=replacement)

    with open(filename) as f:
        assert expected == f.read()

    with pytest.raises(RuntimeError):

        # Calling rewrite_file again should fail since the content
        # has already been updated
        with rewrite_file(filename=filename) as f:

            pattern = r"VERSION = '\d+\.\d+\.\d+'"
            replacement = r"VERSION = '2.0.0'"

            f.regex_replace(pattern=pattern, replacement=replacement)
