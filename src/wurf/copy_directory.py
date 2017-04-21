#! /usr/bin/env python
# encoding: utf-8

import shutil

def copy_directory(path, to_path):
    shutil.copytree(src=path, dst=to_path, symlinks=True)
