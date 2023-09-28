#! /usr/bin/env python
# encoding: utf-8

import os

from .error import DependencyError


class PathResolver(object):
    """
    User Path Resolver functionality. Allows the user to specify the path.
    """

    def __init__(self, dependency, path):
        """Construct an instance.

        :param dependency: A Dependency instance.
        :param path: A path to the dependency
        :param ctx: A Waf Context instance.
        """
        self.dependency = dependency
        self.path = path

    def resolve(self):
        """
        :return: The user specified path.
        """

        self.path = os.path.abspath(os.path.expanduser(self.path))
        if self.dependency.resolver == "http":
            # When using http we may end up with a file rather than
            # a directory
            if not os.path.exists(self.path):
                raise DependencyError(
                    f'Path error: "{self.path}" does not exist.',
                    dependency=self.dependency,
                )
        else:
            if not os.path.isdir(self.path):
                raise DependencyError(
                    f'Path error: "{self.path}" is not a directory.',
                    dependency=self.dependency,
                )
        self.dependency.resolver_info = "path"
        return self.path
