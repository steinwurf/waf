#! /usr/bin/env python
# encoding: utf-8

class WurfSourceParserAction(object):
    """
    """

    def __init__(self, source_actions):
        self.source_actions = source_actions

    def __call__(self, dependency, sources):

        assert(type(sources) is list)
        self.__parse_sources(dependency, sources)

    def __parse_source(self, dependency, source):

        assert(type(source) is dict)

        # First we look for the type in the source description. If
        # it has a type we look for the factory correspoinding to
        # that type
        source_type = source['type']
        del source['type']

        action = self.source_actions[source_type]
        action(dependency, **source)

    def __parse_sources(self, dependency, sources):

        for source in sources:
            self.__parse_source(dependency, source)
