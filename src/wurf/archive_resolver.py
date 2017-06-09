#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


class ArchiveResolver(object):
    """
    Extracts an archive
    """

    def __init__(self, archive_extractor, resolver, cwd):

        """ Construct a new instance.

        :param archive_extractor: An archive (zip, tar, etc.) extractor
            function.
        :param resolver: The parent resolver responsible for downloading the
            archive.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.archive_extractor = archive_extractor
        self.resolver = resolver
        self.cwd = cwd

    def resolve(self):
        """
        :return: The path to the resolved dependency as a string.
        """
        path = self.resolver.resolve()

        assert os.path.isfile(path)

        # Use the path retuned to create a unique location for extracted files
        extract_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        # The folder for storing the requested checkout
        extract_folder = 'extract-' + extract_hash

        extract_path = os.path.join(self.cwd, extract_folder)

        self.archive_extractor(path=path, to_path=extract_path)

        return extract_path
