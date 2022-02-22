#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib

from .url_download import UrlDownload

# This scripts downloads the standalone zipapp version of virtualenv. This is
# to make us independent of what is currently installed on the host OS. For
# example Ubunutu and Debian does not ship with default capabilities to create
# virtual environments.
# We pick the version that supports Python 3.5 since that is the default
# in the oldest Ubuntu LTS currently supported
PYTHON_MAJOR_VERSION = 3
PYTHON_MINOR_VERSION = 5

URL = "https://bootstrap.pypa.io/virtualenv/{}.{}/virtualenv.pyz".format(
    PYTHON_MAJOR_VERSION, PYTHON_MINOR_VERSION
)

# Hash of the pyz file
SHA1 = "d694ddf45b2e64094631e357bc7265f702c222d7"


class VirtualEnvDownload(object):
    def __init__(self, ctx, log, downloader=None, download_path=None):
        """Create a new VirtualEnvDownload instance

        :param ctx: A Waf context
        :param log: A logging object

        :param download_path: The path where the virtualenv should be placed
        """

        self.ctx = ctx
        self.log = log

        if downloader is None:
            self.downloader = UrlDownload()
        else:
            self.downloader = downloader

        if download_path is None:
            self.download_path = self._default_download_path()
        else:
            self.download_path = download_path

    def download(self):
        """Initiate the download"""

        if not os.path.isdir(self.download_path):
            os.makedirs(self.download_path)

        virtualenv_path = os.path.join(self.download_path, "virtualenv.pyz")

        if os.path.isfile(virtualenv_path) and not self._validate(virtualenv_path):
            self.log.debug("Remove corrupted file virtualenv.pyz")
            os.remove(virtualenv_path)

        if not os.path.isfile(virtualenv_path):

            self.log.debug("Downloading {} into {}".format(URL, self.download_path))

            self.downloader.download(
                cwd=self.download_path, source=URL, filename="virtualenv.pyz"
            )

        self.log.debug("Using virtualenv from {}".format(self.download_path))

        if not self._validate(virtualenv_path=virtualenv_path):
            raise RuntimeError("Not valid SHA1 of virtualenv.pyz")

        return virtualenv_path

    def _validate(self, virtualenv_path):
        sha1sum = hashlib.sha1()
        with open(virtualenv_path, "rb") as source:
            block = source.read(2 ** 16)
            while len(block) != 0:
                sha1sum.update(block)
                block = source.read(2 ** 16)

        return sha1sum.hexdigest() == SHA1

    def _default_download_path(self):

        # https://stackoverflow.com/a/4028943
        home_path = os.path.join(os.path.expanduser("~"))
        return os.path.join(
            home_path,
            ".waf-local-virtualenv",
            "{}_{}".format(PYTHON_MAJOR_VERSION, PYTHON_MINOR_VERSION),
        )
