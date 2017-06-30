#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import hashlib

from .directory import remove_directory


class VirtualEnv(object):
    """ Simple object which can be used to work within a virtualevn.

    Example (within a wscript build function):

    def build(bld):

        venv = VirtualEnv.create(cwd='/tmp', ctx=bld, name=None,
            pip_packages_path='/tmp/pip_packages')

        # Will remove the virtualenv when 'with' block is exited
        with venv:
            venv.pip_download('pytest', 'twine')
            venv.pip_local_install('pytest')

            venv.run('python -m pip --version')

    It is important to be aware of the cwd parameter, e.g. if you access files
    etc. it will be relative to cwd. So if cwd is the 'build' directory and you
    access a file in the root of the repository it will need to be prefixed
    with '../somefile.txt'.
    """

    def __init__(self, env, cwd, path, ctx, pip_packages_path):
        """
        Wraps a created virtualenv
        """
        self.env = env
        self.path = path
        self.cwd = cwd
        self.ctx = ctx
        self.pip_packages_path = pip_packages_path

        if 'PATH' in self.env:
            del self.env['PATH']

        if 'PYTHONPATH' in self.env:
            del self.env['PYTHONPATH']

        self.env['PATH'] = os.path.join(path, 'Scripts')

        if sys.platform == 'win32':
            self.env['PATH'] = os.path.join(path, 'Scripts')
        else:
            self.env['PATH'] = os.path.join(path, 'bin')

    def run(self, cmd):
        """ Runs a command in the virtualenv. """
        ret = self.ctx.exec_command(
            cmd, cwd=self.cwd, env=self.env, stdout=None, stderr=None)

        if ret != 0:
            self.ctx.fatal('Exec command "{}" failed!'.format(cmd))

    def pip_download(self, *packages):
        """ Downloads a set of packages from pip.

        :param packages: Package names as string, which should be
            downloaded.
        """
        packages = " ".join(packages)

        self.run('python -m pip download {} --dest {}'.format(
            packages, self.pip_packages_path))

    def pip_local_install(self, *packages):
        """ Installs a set of packages from pip, using local packages from the
        path directory.

        :param packages: Package names as string, which be installed in the
            virtualenv
        """
        packages = " ".join(packages)

        assert(os.path.isdir(self.pip_packages_path))

        self.run('python -m pip install --no-index --find-links={} {}'.format(
            self.pip_packages_path, packages))

    def pip_install(self, *packages):
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
    def create(cwd, env, name, ctx, pip_packages_path):
        """ Create a new virtual env.

        :param cwd: The working directory, as a string, where the virtualenv
            will be created and where the commands will run.
        :param env: The environment to use during creation of the virtualenv,
            once created the PATH and PYTHONPATH variables will be cleared to
            reflect the virtualenv. You must make sure that the virtualenv
            module is avilable. Either as a system package or by specifying the
            PYTHONPATH variable.
        :param name: The name of the virtualenv, as a string. If None a default
            name will be used.
        :param ctx: The Waf Context used to run commands.
        :param pip_packages_path: Path to pip packages (is used when
            downloading/installing pip packages)
        """

        # The Python executable
        python = sys.executable

        if not name:

            # Make a unique virtualenv for different Python executables
            # (e.g. 2.x and 3.x)
            unique = hashlib.sha1(python.encode('utf-8')).hexdigest()[:6]
            name = 'virtualenv-{}'.format(unique)

        # If a virtualenv already exists - lets remove it
        path = os.path.join(cwd, name)
        if os.path.isdir(path):
            remove_directory(path=path)

        # Create the new virtualenv
        args = [python, '-m', 'virtualenv', name, '--no-site-packages']

        ctx.cmd_and_log(args, cwd=cwd, env=env)

        return VirtualEnv(env=env, path=path, cwd=cwd, ctx=ctx,
                          pip_packages_path=pip_packages_path)
