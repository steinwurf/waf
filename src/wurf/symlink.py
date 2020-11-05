#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import subprocess

from .compat import IS_PY2


def create_symlink(from_path, to_path, overwrite=False, relative=False):
    """ Creates a symlink.
    :param from_path: The path to the directory or file we want to create a
        symlink to.
    :param to_path: The path where the symbolic link should be created.
    :param overwrite: If overwrite is True we first remove the path where the
        symbolic link should be created.
    :param relative: If relative is True make the symlink a relative path
    """

    if overwrite and os.path.lexists(path=to_path):
        _remove_symlink(path=to_path)

    print("from_path={}, to_path={}, relative={}".format(
        from_path, to_path, relative))

    # We need this information in the Python2 windows version and we may
    # destroy the from variable when making it relative
    is_directory = os.path.isdir(from_path)

    if relative:

        # If relative we should get the relative path from the location of the
        # symlink to the file or directory we want to point to
        parent_dir = os.path.dirname(to_path)

        from_path = os.path.relpath(from_path, start=parent_dir)

    print("from_path={}, to_path={}, relative={}".format(
        from_path, to_path, relative))

    if IS_PY2 and sys.platform == 'win32':
        _py2_win32_create_symlink(
            from_path=from_path, to_path=to_path, is_directory=is_directory)
    elif IS_PY2:
        _py2_unix_create_symlink(from_path=from_path, to_path=to_path)
    else:
        _py3_create_symlink(from_path=from_path, to_path=to_path)


def _remove_symlink(path):
    if sys.platform == 'win32' and os.path.isdir(path):
        # On Windows, the symlink is not considered a link, but
        # a directory, so it is removed with rmdir. The contents
        # of the original folder will not be removed.
        os.rmdir(path)
    else:
        # On Unix, we remove the symlink with unlink
        os.unlink(path)


def _py2_win32_create_symlink(from_path, to_path, is_directory):

    # os.symlink() is not available in Python 2.7 on Windows.
    # We use the original function if it is available, otherwise we
    # create a helper function for Windows

    # mklink is used to create an NTFS junction, i.e. symlink
    # https://stackoverflow.com/a/22225651/1717320

    cmd = ['mklink']

    if is_directory:
        cmd += ['/J']

    cmd += ['"{}"'.format(to_path.replace('/', '\\')),
            '"{}"'.format(from_path.replace('/', '\\'))]

    # Hide the output of the mklink shell command unless an error happens.
    # If the return code is non-zero, check_output raises a
    # CalledProcessError that contains the return code and the output.
    subprocess.check_output(
        ' '.join(cmd), stderr=subprocess.STDOUT, shell=True)


def _py2_unix_create_symlink(from_path, to_path):
    os.symlink(from_path, to_path)


def _py3_create_symlink(from_path, to_path):
    os.symlink(src=from_path, dst=to_path)
