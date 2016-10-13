#! /usr/bin/env python
# encoding: utf-8

from wurf_dependency_parser import WurfDependencyParser

from wurf_source_parser_action import WurfSourceParserAction
from wurf_optional_parser_action import wurf_optional_parser_action
from wurf_recurse_parser_action import wurf_recurse_parser_action

class WurfDependencyParserFactory(object):
    """

    """

    def __init__(self):
        self.parse_actions = parse_actions
        self.dependency_factory = dependency_factory

    def build(self):



        def parse_git_commit(dependency, url, commit):



        source_actions = {'git_commit': parse_git_commit}

        source_parser = WurfSourceParserAction(source_actions=source_actions)

        parser_actions = {
            'sources': source_parser,
            'optional': wurf_optional_parser_action,
            'recurse': wurf_recurse_parser_action
            }



        parser = WurfDependencyParser()
