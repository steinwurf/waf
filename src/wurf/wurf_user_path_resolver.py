#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil
import sys

class WurfUserPathResolver(object):
    """
    User Path Resolver functionality. Allows the user to specify the path.
    """

    def __init__(self, parser, args):
        """ Construct an instance.

        :param parser: An argpase.ArgumentParser() instance
        """
        self.parser = parser
        self.args = args
        self.parsed_options = {}

    def __parse_arguement(self, name):

        option = '--%s-path' % name

        if option in self.parsed_options:
            return self.parsed_options[option]

        self.parser.add_argument(option, default=None, dest=option)

        known_args, unknown_args = self.parser.parse_known_args(args=self.args)

        # Use vars(...) function to convert argparse.Namespace() to dict
        self.parsed_options = vars(known_args)

        return self.parsed_options[option]

    def resolve(self, name, **kwargs):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """

        return self.__parse_arguement(name)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

from . import wurf_error


class WurfUserPathResolverError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self):
        super(WurfUserPathResolverError, self).__init__(
            "No user path specified")



class WurfUserPathResolver2(object):
    """
    User Path Resolver functionality. Allows the user to specify the path.
    """

    def __init__(self, path):
        """ Construct an instance.

        :param path: Path to the dependency as a string or None of not
            user path has been specified.
        """
        self.path = path

    def resolve(self):
        """
        :return: The user specified path.
        """

        if not self.path:
            raise WurfUserPathResolverError()

        return self.path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
