#! /usr/bin/env python
# encoding: utf-8

import os
import sys


def create_symlink(from_path, to_path, overwrite=False, relative=False):
    """Creates a symlink.
    :param from_path: The path to the directory or file we want to create a
        symlink to.
    :param to_path: The path where the symbolic link should be created.
    :param overwrite: If overwrite is True we first remove the path where the
        symbolic link should be created.
    :param relative: If relative is True make the symlink a relative path
    """

    if overwrite and os.path.lexists(path=to_path):
        _remove_symlink(path=to_path)

    if relative:
        # If relative we should get the relative path from the location of the
        # symlink to the file or directory we want to point to
        parent_dir = os.path.dirname(to_path)

        from_path = os.path.relpath(from_path, start=parent_dir)

    os.symlink(src=from_path, dst=to_path, target_is_directory=os.path.isdir(from_path))


def _remove_symlink(path):
    if sys.platform == "win32" and os.path.isdir(path):
        # On Windows, the symlink is not considered a link, but
        # a directory, so it is removed with rmdir. The contents
        # of the original folder will not be removed.
        os.rmdir(path)
    else:
        # On Unix, we remove the symlink with unlink
        os.unlink(path)
