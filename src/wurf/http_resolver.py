#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


class HttpResolver(object):
    """
    Http Resolver functionality. Downloads a file.
    """

    def __init__(self, urlopen, dependency, source, cwd):

        """ Construct a new instance.

        :param urlopen: The Python URL open function
        :param dependency: The dependency instance.
        :param source: The URL of the dependency as a string
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.urlopen = urlopen
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

        file_name = os.path.basename(self.source)
        file_path = os.path.join(folder_path, file_name)

        # If the download file does not exist download it
        if not os.path.isfile(file_path):

            # From http://stackoverflow.com/a/1517728
            response = self.urlopen(url=self.source)
            CHUNK = 16 * 1024
            with open(file_path, 'wb') as f:
                while True:
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)

        else:
            # We only want to download if a newer file exists on the server
            # can we check that here?
            pass

        assert os.path.isfile(file_path), "We should have a valid path here!"

        return file_path
