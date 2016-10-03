#! /usr/bin/env python
# encoding: utf-8

def wurf_optional_parser_action(dependency, optional):
    """ Sets the optional attribute of a dependency. """

    assert(type(optional) is bool)
    dependency.optional = optional
