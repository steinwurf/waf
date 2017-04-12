#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


class HttpResolver(object):
    """
    Http Resolver functionality. Downloads a file.
    """

    def __init__(self, urldownload, dependency, source, cwd):

        """ Construct a new instance.

        :param urldownload: An UrlDownload instance
        :param dependency: The dependency instance.
        :param source: The URL of the dependency as a string
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.urldownload = urldownload
        self.dependency = dependency
        self.source = source
        self.cwd = cwd

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """
        # Store the current source in the dependency object
        self.dependency.current_source = self.source

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        source_hash = hashlib.sha1(self.source.encode('utf-8')).hexdigest()[:6]

        # The folder for storing the file
        folder_name = 'http-' + source_hash
        folder_path = os.path.join(self.cwd, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if dependency.filename:
            filename = dependency.filename
        else:
            filename = None

        file_path = self.urldownload.download(cwd=folder_path, url=self.source,
            filename=filename)

        assert os.path.isfile(file_path), "We should have a valid path here!"

        return file_path
