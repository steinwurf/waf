#!/usr/bin/env python
# encoding: utf-8

import os

from wurf.symlink import create_symlink


def test_symlink_directory(testdirectory):

    foo_dir = testdirectory.mkdir('foo')
    link_dir = os.path.join(testdirectory.path(), 'foo-link')

    assert not os.path.exists(link_dir)

    create_symlink(from_path=foo_dir.path(), to_path=link_dir)

    assert os.path.exists(link_dir)
