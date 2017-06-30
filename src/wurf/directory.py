#! /usr/bin/env python
# encoding: utf-8

import shutil
import stat
import os


def copy_directory(path, to_path):

    # In Python2 convert to unicode
    try:
        path = unicode(path)
        to_path = unicode(to_path)
    except NameError:
        pass

    shutil.copytree(src=path, dst=to_path, symlinks=True)


def remove_directory(path):

    # In Python2 convert to unicode
    try:
        path = unicode(path)
    except NameError:
        pass

    # Note that shutil.rmtree fails if there are any broken symlinks in that
    # folder, so we use os.walk to traverse the directory tree from the bottom
    # up as recommended here:
    # http://stackoverflow.com/a/2656408

    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if not os.path.islink(filename):
                os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            dir = os.path.join(root, name)
            if os.path.islink(dir):
                os.unlink(dir)
            else:
                os.rmdir(dir)

    os.rmdir(path)
