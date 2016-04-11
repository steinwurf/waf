#! /usr/bin/env python
# encoding: utf-8

class WurfResolveAction:
    """The resolve actions supported by the WurfDependency.

    USER: The user has specified a path on the file system which
    contains the dependency.

    FETCH: The resolver should fetch the dependency to the bundle path.

    LOAD: The path for the dependency should be loaded from the
    dependency config.

    Using all capitalized for the names:
    https://www.python.org/dev/peps/pep-0008/#constants
    """
    USER, FETCH, LOAD = range(3)
