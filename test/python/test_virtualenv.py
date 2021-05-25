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
    ctx.path.abspath = lambda: testdirectory.path()
    log = mock.Mock()

    venv = VirtualEnv.create(cwd=cwd, env=env, name=name, log=log, ctx=ctx)

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, "virtualenv-*"))


def test_virtualenv_name(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = "gogo"
    ctx = mock.Mock()
    ctx.path.abspath = lambda: testdirectory.path()
    log = mock.Mock()

    # Lets make the directory to make sure it is removed
    testdirectory.mkdir(name)
    assert testdirectory.contains_dir(name)

    venv = VirtualEnv.create(
        log=log,
        cwd=cwd,
        env=env,
        name=name,
        ctx=ctx,
        system_site_packages=True,
        download=False,
    )

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, name))
    assert not testdirectory.contains_dir(name)

    ctx.cmd_and_log.assert_called_once_with(
        [sys.executable, "-m", "virtualenv", name, "--system-site-packages"],
        cwd=cwd,
        env=env,
    )

    venv.run("python -m pip install pytest")

    ctx.exec_command.assert_called_once_with(
        "python -m pip install pytest",
        cwd=venv.cwd,
        env=venv.env,
        stdout=None,
        stderr=None,
    )


def test_virtualenv_system_site_packages(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = "gogo"
    ctx = mock.Mock()
    ctx.path.abspath = lambda: testdirectory.path()
    log = mock.Mock()

    # Lets make the directory to make sure it is removed
    testdirectory.mkdir(name)
    assert testdirectory.contains_dir(name)

    venv = VirtualEnv.create(
        log=log,
        cwd=cwd,
        env=env,
        name=name,
        ctx=ctx,
        system_site_packages=False,
        download=False,
    )

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, name))
    assert not testdirectory.contains_dir(name)

    ctx.cmd_and_log.assert_called_once_with(
        [sys.executable, "-m", "virtualenv", name], cwd=cwd, env=env
    )

    venv.run("python -m pip install pytest")

    ctx.exec_command.assert_called_once_with(
        "python -m pip install pytest",
        cwd=venv.cwd,
        env=venv.env,
        stdout=None,
        stderr=None,
    )
