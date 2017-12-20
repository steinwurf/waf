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
    assert os.path.isdir(link_dir)


def test_symlink_file(testdirectory):
    sub1 = testdirectory.mkdir('sub1')
    sub2 = testdirectory.mkdir('sub2')

    ok_path = sub1.write_text('ok.txt', u'hello_world', encoding='utf-8')

    # Create a symlink to 'ok.txt' inside sub2
    link_path = os.path.join(sub2.path(), 'ok.txt')
    create_symlink(from_path=ok_path, to_path=link_path)

    assert sub2.contains_file('ok.txt')
    assert os.path.isfile(link_path)
