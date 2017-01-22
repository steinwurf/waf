#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil
import sys

from . import wurf_error


class UserPathResolverError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self):
        super(UserPathResolverError, self).__init__(
            "No user path specified")

class UserPathResolver(object):
    """
    User Path Resolver functionality. Allows the user to specify the path.
    """

    def __init__(self, path):
        """ Construct an instance.

        :param path: Path to the dependency as a string or None of not
            user path has been specified.
        """
        assert os.path.isdir(path)
        self.path = path

    def resolve(self):
        """
        :return: The user specified path.
        """
        return self.path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
