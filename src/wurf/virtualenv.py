#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import hashlib

from .directory import remove_directory


class VirtualEnv(object):
    """Simple object which can be used to work within a virtualenv.

    Example (within a wscript build function):

    def build(bld):

        venv = VirtualEnv.create(cwd='/tmp', ctx=bld, name=None)

        # Will remove the virtualenv when 'with' block is exited
        with venv:
            venv.run('python -m pip install pytest')
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

        # Make sure the virtualenv Python executable is first in PATH
        if sys.platform == "win32":
            python_path = os.path.join(path, "Scripts")
        else:
            python_path = os.path.join(path, "bin")

        self.env["PATH"] = os.path.pathsep.join([python_path, env["PATH"]])

    def run(self, cmd, cwd=None):
        """Runs a command in the virtualenv.

        :param cmd: The command to run.
        :param cwd: The working directory i.e. where to run the command. If not
            specified the cwd used to create the virtual env will be used.
        """
        if not cwd:
            cwd = self.cwd

        ret = self.ctx.exec_command(
            cmd, cwd=cwd, env=self.env, stdout=None, stderr=None
        )

        if ret != 0:
            self.ctx.fatal(f'Exec command "{cmd}" failed!')

    def __enter__(self):
        """When used in a with statement the virtualenv will be automatically
        revmoved.
        """
        return self

    def __exit__(self, type, value, traceback):
        """Remove the virtualenv."""
        remove_directory(path=self.path)

    @staticmethod
    def check_venv():
        """Checks if the venv is available."""
        try:
            import ensurepip

            # Silence pyflakes on unused imports
            assert ensurepip

            return True
        except ImportError:
            return False

    @staticmethod
    def check_virtualenv():
        """Checks if the virtualenv is available."""
        try:
            import virtualenv

            # Silence pyflakes on unused imports
            assert virtualenv
            return True
        except ImportError:
            return False

    @staticmethod
    def create(
        ctx,
        log,
        cwd=None,
        env=None,
        name=None,
        overwrite=True,
        system_site_packages=False,
    ):
        """Create a new virtual env.

        :param ctx: The Waf Context used to run commands.
        :param log: The logging object to use
        :param cwd: The working directory, as a string, where the virtualenv
            will be created and where the commands will run.
        :param env: The environment to use during creation of the virtualenv,
            once created the PATH and PYTHONPATH variables will be cleared to
            reflect the virtualenv. You must make sure that the virtualenv
            module is available. Either as a system package or by specifying the
            PYTHONPATH variable.
        :param name: The name of the virtualenv, as a string. If None a default
            name will be used.
        :param overwrite: If an existing virtualenv with the same name already
            exists we will overwrite it. To reuse the virtualenv pass
            overwrite=False.
        :param system_site_packages: If true give the virtual environment access
               to the global site-packages.
        """

        # The Python executable
        python = sys.executable

        if not cwd:
            # Use the working directory of the waf context
            cwd = ctx.path.abspath()

        # Check if the cwd is a subdirectory of the build folder. It's a bad
        # idea to create the virtualenv in the build folder. Reason being that
        # virtualenv will create symlinks to the Python interpreter and other
        # stuff - if those are create in the build folder waf will try to
        # delete them when running waf clean.
        if cwd.startswith(os.path.join(ctx.path.abspath(), "build")):
            ctx.fatal(
                "Cannot create virtualenv inside the build folder. "
                "Virtualenv create symlinks to files that will be "
                "deleted with 'waf clean'."
            )

        if not env:
            # Use the current environment
            env = dict(os.environ)

        # We should delete the PYTHONPATH variable if it exists. Since
        # otherwise already installed packages might get in our way e.g.:
        # https://stackoverflow.com/a/15887589/1717320

        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]

        if not name:
            # Make a unique virtualenv for different Python executables
            # (e.g. 2.x and 3.x)
            unique = hashlib.sha1(python.encode("utf-8")).hexdigest()[:6]
            name = f"virtualenv-{unique}"

        path = os.path.join(cwd, name)

        # If a virtualenv already exists - and overwrite is True
        # lets remove it
        if os.path.isdir(path) and overwrite:
            remove_directory(path=path)

        if os.path.isdir(path):
            # The virtualenv already exists lets use that...
            return VirtualEnv(env=env, path=path, cwd=cwd, ctx=ctx)

        if VirtualEnv.check_venv():
            # Use the venv module
            cmd = [python, "-m", "venv", name]

        elif VirtualEnv.check_virtualenv():
            # If virtualenv is not install it likely means that you are on a
            # Debian based system (e.g. Ubuntu). The issue with Debian is that
            # they decided to split Python into multiple sub-packages. Which
            # means that it does not ship with a bunch of internal libraries
            # e.g. venv support for ensurepip and distutils

            # Use the virtualenv module
            cmd = [python, "-m", "virtualenv", "--python", python, name]

        else:
            # No virtualenv module available
            #
            # You may boostrap a virtualenv or pip by using pypi e.g. from here
            # https://bootstrap.pypa.io/ or the github repositories. However,
            # it will not help since distutils is still missing and there is no
            # bootstrapping packages available for that.

            ctx.fatal(
                "Cannot create virtual environment due to missing Python support. "
                "If on Debian/Ubuntu virtualenv support can be added by "
                "running 'apt install python3-venv'."
            )

        if system_site_packages:
            cmd += ["--system-site-packages"]

        # Create virtual envionment
        ctx.cmd_and_log(cmd, cwd=cwd, env=env)

        return VirtualEnv(env=env, path=path, cwd=cwd, ctx=ctx)
