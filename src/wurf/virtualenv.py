#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import hashlib

from .directory import remove_directory
from .compat import IS_PY2


class VirtualEnv(object):
    """ Simple object which can be used to work within a virtualevn.

    Example (within a wscript build function):

    def build(bld):

        venv = VirtualEnv.create(cwd='/tmp', ctx=bld, name=None)

        # Will remove the virtualenv when 'with' block is exited
        with venv:
            venv.pip_local_download(
                pip_packages_path='/tmp/pip_packages',
                packages=['pytest', 'twine'])

            venv.pip_local_install(
                pip_packages_path='/tmp/pip_packages',
                packages=['pytest'])

            venv.run('python -m pip --version')

    It is important to be aware of the cwd parameter, e.g. if you access files
    etc. it will be relative to cwd. So if cwd is the 'build' directory and you
    access a file in the root of the repository it will need to be prefixed
    with '../somefile.txt'.
    """

    def __init__(self, env, cwd, path, ctx):
        """
        Wraps a created virtualenv
        """
        self.env = env
        self.path = path
        self.cwd = cwd
        self.ctx = ctx

        if 'PATH' in self.env:
            del self.env['PATH']

        if 'PYTHONPATH' in self.env:
            del self.env['PYTHONPATH']

        self.env['PATH'] = os.path.join(path, 'Scripts')

        if sys.platform == 'win32':
            self.env['PATH'] = os.path.join(path, 'Scripts')
        else:
            self.env['PATH'] = os.path.join(path, 'bin')

    def run(self, cmd, cwd=None):
        """ Runs a command in the virtualenv.

        :param cmd: The command to run.
        :param cwd: The working directory i.e. where to run the command. If not
            specified the cwd used to create the virtual env will be used.
        """
        if not cwd:
            cwd = self.cwd

        ret = self.ctx.exec_command(
            cmd, cwd=cwd, env=self.env, stdout=None, stderr=None)

        if ret != 0:
            self.ctx.fatal('Exec command "{}" failed!'.format(cmd))

    def pip_local_download(self, pip_packages_path, packages):
        """ Downloads a set of packages from pip.

        :param pip_packages_path: Path to pip packages (is used when
            downloading/installing pip packages)
        :param packages: Package names as string, which should be
            downloaded.
        """
        packages = " ".join(packages)

        self.run('python -m pip download {} --dest {}'.format(
            packages, pip_packages_path))

    def pip_local_install(self, pip_packages_path, packages):
        """ Installs a set of packages from pip, using local packages from the
        path directory.

        :param pip_packages_path: Path to pip packages (is used when
            downloading/installing pip packages)
        :param packages: Package names as string, which be installed in the
            virtualenv
        """
        packages = " ".join(packages)

        assert(os.path.isdir(pip_packages_path))

        self.run('python -m pip install --no-index --find-links={} {}'.format(
            pip_packages_path, packages))

    def pip_install(self, packages):
        """ Installs a set of packages from pip

        :param packages: Package names as string, which be installed in the
            virtualenv
        """
        packages = " ".join(packages)

        self.run('python -m pip install {}'.format(packages))

    def __enter__(self):
        """ When used in a with statement the virtualenv will be automatically
        revmoved.
        """
        return self

    def __exit__(self, type, value, traceback):
        """ Remove the virtualenv. """
        remove_directory(path=self.path)

    @staticmethod
    def create(ctx, cwd=None, env=None, name=None):
        """ Create a new virtual env.

        :param ctx: The Waf Context used to run commands.
        :param cwd: The working directory, as a string, where the virtualenv
            will be created and where the commands will run.
        :param env: The environment to use during creation of the virtualenv,
            once created the PATH and PYTHONPATH variables will be cleared to
            reflect the virtualenv. You must make sure that the virtualenv
            module is avilable. Either as a system package or by specifying the
            PYTHONPATH variable.
        :param name: The name of the virtualenv, as a string. If None a default
            name will be used.
        """

        # The Python executable
        python = sys.executable

        if not cwd:
            # Use the working directory of the waf context
            cwd = ctx.path.abspath()

        if not env:
            # Use the current environment
            env = dict(os.environ)

        if not name:

            # Make a unique virtualenv for different Python executables
            # (e.g. 2.x and 3.x)
            unique = hashlib.sha1(python.encode('utf-8')).hexdigest()[:6]
            name = 'virtualenv-{}'.format(unique)

        # If a virtualenv already exists - lets remove it
        path = os.path.join(cwd, name)
        if os.path.isdir(path):
            remove_directory(path=path)

        if IS_PY2:
            # Create the new virtualenv - requires the virtualenv module to
            # be available
            cmd = [python, '-m', 'virtualenv', name, '--no-site-packages']
        else:
            # In Python3 we have venv. The default behavior of venv is to
            # not expose system packages.
            cmd = cmd = [python, '-m', 'venv', name]

        ctx.cmd_and_log(cmd, cwd=cwd, env=env)

        return VirtualEnv(env=env, path=path, cwd=cwd, ctx=ctx)
