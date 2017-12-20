#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import subprocess

from .compat import IS_PY2


def create_symlink(from_path, to_path, overwrite=False):

    if IS_PY2 and sys.platform == 'win32':
        _py2_win32_create_symlink(from_path=from_path, to_path=to_path)
    elif IS_PY2:
        _py2_unix_create_symlink(from_path=from_path, to_path=to_path)
    else:
        _py3_create_symlink(from_path=from_path, to_path=to_path)


def _py2_win32_create_symlink(from_path, to_path):

    # os.symlink() is not available in Python 2.7 on Windows.
    # We use the original function if it is available, otherwise we
    # create a helper function for Windows

    # mklink is used to create an NTFS junction, i.e. symlink
    # https://stackoverflow.com/a/22225651/1717320
    cmd = 'mklink /J "{}" "{}"'.format(
        to_path.replace('/', '\\'), from_path.replace('/', '\\'))
    subprocess.call(cmd, shell=True)


def _py2_unix_create_symlink(from_path, to_path):
    os.symlink(from_path, to_path)


def _py3_create_symlink(from_path, to_path):
    os.symlink(src=from_path, dst=to_path)
