#!/usr/bin/env python
# encoding: utf-8

import os

from wurf.directory import copy_directory
from wurf.directory import remove_directory

def test_directory(test_directory):

    foo_dir = test_directory.mkdir('foo')
    foo_dir.write_text('test.txt', data='ok', encoding='utf-8')

    copy_directory(path=foo_dir.path(),
        to_path=os.path.join(test_directory.path(), 'bar'))

    bar_dir = test_directory.join('bar')

    assert bar_dir.contains_file('test.txt')

def test_directory_unicode(test_directory):

    foo_dir = test_directory.mkdir(u'foo')
    foo_dir.write_binary(u'圧縮.zip', data=b'ok')

    copy_directory(path=foo_dir.path(),
        to_path=os.path.join(test_directory.path(), u'bar'))

    bar_dir = test_directory.join(u'bar')

    assert bar_dir.contains_file(u'圧縮.zip')
