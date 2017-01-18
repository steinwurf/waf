import os
import sys
import subprocess
import glob
import time
import mock
import functools

import shutilwhich
import semver


def test_copy_file(test_directory):
    test_directory.copy_files('test/prog1/*')
    test_directory.copy_file('build/waf')

    print(test_directory.path())

    r = test_directory.run('python','waf','configure')

    assert r.returncode == 0
    assert r.stdout.match('*finished successfully*')

    r = test_directory.run('python', 'waf', 'build')

    assert r.returncode == 0



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
