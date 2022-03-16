#! /usr/bin/env python
# encoding: utf-8

import os

from .git import Git

# This scripts downloads the standalone zipapp version of virtualenv. This is
# to make us independent of what is currently installed on the host OS. For
# example Ubuntu and Debian does not ship with default capabilities to create
# virtual environments.
#
# We pick the version that supports Python 3.5 since that is the default
# in the oldest Ubuntu LTS currently supported

PYTHON_MAJOR_VERSION = 3
PYTHON_MINOR_VERSION = 5

URL = "https://github.com/pypa/get-virtualenv"
VERSION = "20.13.3"


class VirtualEnvDownload(object):
    def __init__(self, ctx, log, git=None, download_path=None):
        """Create a new VirtualEnvDownload instance

        :param ctx: A Waf context
        :param log: A logging object
        :param git: The Git object to use
        :param download_path: The path where the virtualenv should be placed
        """

        self.ctx = ctx
        self.log = log

        if git is None:
            self.git = Git(git_binary="git", ctx=self.ctx)
        else:
            self.git = git

        if download_path is None:
            self.download_path = self._default_clone_path()
        else:
            self.download_path = download_path

    def download(self):
        """Initiate the download"""

        if not os.path.isdir(self.download_path):
            os.makedirs(self.download_path)

        repo_path = os.path.join(self.download_path, VERSION)

        if not os.path.isdir(repo_path):

            self.log.debug("Cloning {} into {}".format(URL, repo_path))

            self.git.clone(
                repository=URL,
                directory=repo_path,
                cwd=self.download_path,
                depth=1,
                branch=VERSION,
            )

        self.log.debug("Using get-virtualenv from {}".format(repo_path))

        zipapp_path = os.path.join(
            repo_path,
            "public",
            "{}.{}".format(PYTHON_MAJOR_VERSION, PYTHON_MINOR_VERSION),
            "virtualenv.pyz",
        )

        return zipapp_path

    def _default_clone_path(self):

        # https://stackoverflow.com/a/4028943
        home_path = os.path.join(os.path.expanduser("~"))
        return os.path.join(home_path, ".waf-local-get-virtualenv")
