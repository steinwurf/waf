#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib

class ParentFolder(object):
    """
    Determines a parent folder where different versions of a given
    dependency can be stored.
    """

    def __init__(self, resolve_path):
        """ Construct a new instance.

        :param resolve_path: Current working directory as a string. This is
            the place where we should create new folders etc.
        """
        self.resolve_path = resolve_path

        assert os.path.isabs(self.resolve_path)

    def parent_folder(self, name, source):
        """
        Determines the parent folder to store different versions of this
        dependency.

        :param name: The name of the dependency as a string
        :param source: The URL of the dependency as a string

        :return: The path to the parent folder as a string.
        """

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(source.encode('utf-8')).hexdigest()[:6]

        repo_folder = os.path.join(
            self.resolve_path, '{}-{}'.format(name, repo_hash))

        return repo_folder

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
