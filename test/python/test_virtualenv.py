#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import mock
import fnmatch

from wurf.venv import VEnv


def test_venv_noname(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = None
    ctx = mock.Mock()
    ctx.path.abspath = lambda: testdirectory.path()

    venv = VEnv.create(cwd=cwd, env=env, name=name, ctx=ctx)

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, "venv-*"))


def test_venv_name(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = "gogo"
    ctx = mock.Mock()
    ctx.path.abspath = lambda: testdirectory.path()

    # Lets make the directory to make sure it is removed
    testdirectory.mkdir(name)
    assert testdirectory.contains_dir(name)

    venv = VEnv.create(
        cwd=cwd,
        env=env,
        name=name,
        ctx=ctx,
        system_site_packages=True,
    )

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, name))
    assert not testdirectory.contains_dir(name)

    ctx.cmd_and_log.assert_called_once_with(
        [sys.executable, "-m", "venv", name, "--system-site-packages"],
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


def test_venv_system_site_packages(testdirectory):

    cwd = testdirectory.path()
    env = dict(os.environ)
    name = "gogo"
    ctx = mock.Mock()
    ctx.path.abspath = lambda: testdirectory.path()

    # Lets make the directory to make sure it is removed
    testdirectory.mkdir(name)
    assert testdirectory.contains_dir(name)

    venv = VEnv.create(
        cwd=cwd,
        env=env,
        name=name,
        ctx=ctx,
        system_site_packages=False,
    )

    assert fnmatch.fnmatch(venv.path, os.path.join(cwd, name))
    assert not testdirectory.contains_dir(name)

    ctx.cmd_and_log.assert_called_once_with(
        [sys.executable, "-m", "venv", name], cwd=cwd, env=env
    )

    venv.run("python -m pip install pytest")

    ctx.exec_command.assert_called_once_with(
        "python -m pip install pytest",
        cwd=venv.cwd,
        env=venv.env,
        stdout=None,
        stderr=None,
    )
