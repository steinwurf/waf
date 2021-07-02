#! /usr/bin/env python
# encoding: utf-8


class ListResolver(object):
    """Iterates through a list of resolvers until a path is resolved."""

    def __init__(self, resolvers):
        """Construct an instance.

        :param resolvers: A list of resolvers object for the available
           sources
        """
        self.resolvers = resolvers

    def resolve(self):
        """Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        for resolver in self.resolvers:

            path = resolver.resolve()

            if path:
                return path
        else:
            return None
