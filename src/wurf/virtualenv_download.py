#! /usr/bin/env python
# encoding: utf-8

import os

from .git import Git

URL = "https://github.com/pypa/virtualenv.git"
VERSION = "16.4.3"


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

        self.log.debug("Using virtualenv from {}".format(repo_path))

        return repo_path

    def _default_clone_path(self):

        # https://stackoverflow.com/a/4028943
        home_path = os.path.join(os.path.expanduser("~"))
        return os.path.join(home_path, ".waf-local-virtualenv")
