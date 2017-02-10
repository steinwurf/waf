import os
import sys
import subprocess
import glob
import time
import mock
import functools

import shutilwhich
import semver

# TODO: Kill or rewrite this test file!

def test_working_on_it(test_directory):


    dep = {"name":"waf", "patches": ["patches/patch01.patch",
           "patches/patch02.patch"], "optional":True,
           "sources":[{"resolver":"git", "url":"gitrepo.git"}]}

    ctx = mock.Mock()
    log = mock.Mock()
    git_binary = '/bin/git'

    # registry = wurf_registry.build_registry(
    #     ctx=ctx, log=log, git_binary=git_binary)

    #assert(f.color() == "red")
