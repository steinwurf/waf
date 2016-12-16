#! /usr/bin/env python
# encoding: utf-8

import hashlib
import json

class WurfHashManager(object):
    def __init__(self):
        """ Construct an instance."""
        # The next resolver to handle the dependency
        self.next_resolver = None


    def add_dependency(self, **kwargs):
        """ Hash the dependency options.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        # Make sure the sha1 hash is not already included
        assert('sha1' not in kwargs)

        sha1 = self.__hash_dependency(**kwargs)

        self.next_resolver.add_dependency(sha1=sha1, **kwargs)

    def __hash_dependency(self, **kwargs):
        """ Hash the keyword arguments representing the  to the dependency.

        :return: Hash of the dependency as a string.
        """

        s = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha1(s.encode('utf-8')).hexdigest()

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
