#! /usr/bin/env python
# encoding: utf-8

def wurf_recurse_parser_action(dependency, recurse):
    """ Sets the recurse attribute of a dependency. """

    assert(type(recurse) is bool)
    dependency.recurse = recurse
