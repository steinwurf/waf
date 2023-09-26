#! /usr/bin/env python
# encoding: utf-8

import os


class HttpResolver(object):
    """
    Http Resolver functionality. Downloads a file.
    """

    def __init__(self, url_download, dependency, cwd):
        """Construct a new instance.

        :param url_download: An UrlDownload instance
        :param dependency: The dependency instance.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.url_download = url_download
        self.dependency = dependency
        self.cwd = cwd

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        # The folder for storing the file
        folder_path = os.path.join(self.cwd, "download")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if self.dependency.filename:
            filename = self.dependency.filename
        else:
            filename = None

        file_path = self.url_download.download(
            cwd=folder_path, source=self.dependency.source, filename=filename
        )
        assert os.path.isfile(file_path), "We should have a valid path here!"

        self.dependency.resolver_info = os.path.basename(file_path)

        return file_path
