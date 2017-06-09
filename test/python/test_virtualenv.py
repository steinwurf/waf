#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import mock
import fnmatch

from wurf.virtualenv import VirtualEnv


def test_virtualenv_noname(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = None
    ctx = mock.Mock()
    pip_packages_path = '/tmp/pip_packages'

    venv = VirtualEnv.create(cwd=cwd, env=env, name=name, ctx=ctx,
                             pip_packages_path=pip_packages_path)

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, 'virtualenv-*'))


def test_virtualenv_name(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = 'gogo'
    ctx = mock.Mock()

    pip_packages_dir = testdirectory.mkdir('pip_packages')

    # Lets make the directory to make sure it is removed
    testdirectory.mkdir(name)
    assert testdirectory.contains_dir(name)

    venv = VirtualEnv.create(cwd=cwd, env=env, name=name, ctx=ctx,
                             pip_packages_path=pip_packages_dir.path())

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, name))
    assert not testdirectory.contains_dir(name)

    ctx.cmd_and_log.assert_called_once_with(
        [sys.executable, '-m', 'virtualenv', name, '--no-site-packages'],
        cwd=cwd, env=env)

    venv.pip_download('pytest', 'twine')

    ctx.exec_command.assert_called_once_with(
        'python -m pip download pytest twine --dest {}'.format(
            pip_packages_dir.path()),
        cwd=venv.cwd, env=venv.env, stdout=None, stderr=None)

    # Reset state
    ctx.exec_command = mock.Mock()

    # We have to make sure the pip_packages_path exists
    venv.pip_local_install('pytest', 'twine')

    ctx.exec_command.assert_called_once_with(
        'python -m pip install --no-index --find-links={} pytest twine'.format(
            pip_packages_dir.path()),
        cwd=venv.cwd, env=venv.env, stdout=None, stderr=None)
