#!/usr/bin/env python
# encoding: utf-8

import os
import pytest
import mock
import fnmatch

from wurf.virtualenv import VirtualEnv

def test_virtualenv_noname(test_directory):

    cwd = test_directory.path()
    env = dict(os.environ)
    name = None
    ctx = mock.Mock()
    pip_packages_path = '/tmp/pip_packages'

    venv = VirtualEnv.create(cwd=cwd, env=env, name=name, ctx=ctx,
        pip_packages_path=pip_packages_path)

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, 'virtualenv-*'))

    ctx.cmd_and_log.assert_called_once_with(
        ['/bin/git_binary','clone','https://github.com/repo.git','/tmp/repo2'],
        cwd=cwd, env=env)



def test_virtualenv_name(test_directory):

    cwd = test_directory.path()
    env = dict(os.environ)
    name = 'gogo'
    ctx = mock.Mock()
    pip_packages_path = '/tmp/pip_packages'

    # Lets make the directory to make sure it is removed
    test_directory.mkdir('okok')
    assert test_directory.contains_dir('okok')

    venv = VirtualEnv.create(cwd=cwd, env=env, name=name, ctx=ctx,
        pip_packages_path=pip_packages_path)

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, 'gogo'))
    assert not test_directory.contains_dir('okok')
