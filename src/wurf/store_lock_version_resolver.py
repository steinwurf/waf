#! /usr/bin/env python
# encoding: utf-8

import os
import json
import shutil

from .error import Error

class StoreLockVersionResolver(object):

    def __init__(self, resolver, lock_cache, dependency):
        """ Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param lock_cache: The lock cache to store the version information in.
        :param dependency: A Dependency instance.
        """
        self.resolver = resolver
        self.lock_cache = lock_cache
        self.dependency = dependency

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "active" resolver, meaning that waf was invoked with
        configure. Then we save the resolved checkout to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        checkout = None

        if self.dependency.git_tag:
            checkout = self.dependency.git_tag
        elif self.dependency.git_commit:
            checkout = self.dependency.git_commit
        else:
            raise Error('Not stable checkout information found.')

        self.lock_cache.add_checkout(dependency=self.dependency,
            checkout=checkout)

        return path
