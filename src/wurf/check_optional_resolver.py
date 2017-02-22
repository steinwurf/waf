#! /usr/bin/env python
# encoding: utf-8

from .error import DependencyError

class CheckOptionalResolver(object):

    def __init__(self, resolver, dependency):
        """ Construct an instance.

        :param resolver: The resolver used to fecth the dependency
        :param dependency: The Dependency object.
        """
        self.resolver = resolver
        self.dependency = dependency

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        if not path and not self.dependency.optional:
            raise DependencyError(msg="Non-optional dependency failed.",
                dependency=self.dependency)

        return path
