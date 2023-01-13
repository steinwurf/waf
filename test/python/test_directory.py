#!/usr/bin/env python
# encoding: utf-8

import os

from wurf.directory import copy_directory
from wurf.directory import remove_directory


def testdirectory(testdirectory):

    foo_dir = testdirectory.mkdir("foo")
    foo_dir.write_text("test.txt", data="ok", encoding="utf-8")

    copy_directory(
        path=foo_dir.path(), to_path=os.path.join(testdirectory.path(), "bar")
    )

    bar_dir = testdirectory.join("bar")

    assert bar_dir.contains_file("test.txt")

    assert testdirectory.contains_dir(foo_dir.path())
    assert testdirectory.contains_dir(bar_dir.path())

    remove_directory(foo_dir.path())
    remove_directory(bar_dir.path())

    assert not testdirectory.contains_dir(foo_dir.path())
    assert not testdirectory.contains_dir(bar_dir.path())


def testdirectory_unicode(testdirectory):

    foo_dir = testdirectory.mkdir("foo")
    foo_dir.write_binary("圧縮.zip", data=b"ok")

    copy_directory(
        path=foo_dir.path(), to_path=os.path.join(testdirectory.path(), "bar")
    )

    bar_dir = testdirectory.join("bar")

    assert bar_dir.contains_file("圧縮.zip")

    assert testdirectory.contains_dir(foo_dir.path())
    assert testdirectory.contains_dir(bar_dir.path())

    remove_directory(foo_dir.path())
    remove_directory(bar_dir.path())

    assert not testdirectory.contains_dir(foo_dir.path())
    assert not testdirectory.contains_dir(bar_dir.path())
