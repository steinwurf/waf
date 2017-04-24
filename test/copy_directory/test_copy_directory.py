#!/usr/bin/env python
# encoding: utf-8

import os

from wurf.copy_directory import copy_directory

def test_copy_directory(test_directory):

    foo_dir = test_directory.mkdir('foo')
    foo_dir.write_file('test.txt', 'ok')

    copy_directory(path=foo_dir.path(),
        to_path=os.path.join(test_directory.path(), 'bar'))

    bar_dir = test_directory.join('bar')

    assert bar_dir.contains_file('test.txt')

def test_copy_directory(test_directory):

    foo_dir = test_directory.mkdir(u'foo')
    foo_dir.write_file(u'圧縮.zip', 'ok')

    copy_directory(path=foo_dir.path(),
        to_path=os.path.join(test_directory.path(), u'bar'))

    bar_dir = test_directory.join(u'bar')

    assert bar_dir.contains_file(u'圧縮.zip')
