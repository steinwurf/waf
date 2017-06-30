#! /usr/bin/env python
# encoding: utf-8

from .error import TopLevelError


class MandatoryResolver(object):
    """ Iterates through a list of resolvers until a path is resolved."""

    def __init__(self, resolver, msg, dependency):
        """ Construct an instance.

        :param resolvers: A list of resolvers object for the available
           sources
        """
        self.resolver = resolver
        self.msg = msg
        self.dependency = dependency

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """
        path = self.resolver.resolve()

        if not path:
            raise TopLevelError(msg=self.msg, dependency=self.dependency)

        return path
