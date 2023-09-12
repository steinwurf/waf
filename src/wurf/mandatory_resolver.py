#! /usr/bin/env python
# encoding: utf-8

from .error import TopLevelError


class MandatoryResolver(object):
    """Iterates through a list of resolvers until a path is resolved."""

    def __init__(self, resolver, msg, dependency):
        """Construct an instance.

        :param resolver: The resolver to use
        :param msg: The error message to display if the dependency is not found
        :param dependency: The dependency to resolve
        """
        self.resolver = resolver
        self.msg = msg
        self.dependency = dependency

    def resolve(self):
        """Resolve the dependency.

        :return: Path to resolved dependency as a string
        """
        path = self.resolver.resolve()

        if not path:
            raise TopLevelError(msg=self.msg, dependency=self.dependency)

        return path
