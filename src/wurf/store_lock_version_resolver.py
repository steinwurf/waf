#! /usr/bin/env python
# encoding: utf-8

from .lock_version_cache import LockVersionCache


class StoreLockVersionResolver(object):
    def __init__(self, resolver, lock_cache_to: LockVersionCache, dependency):
        """Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param lock_cache_to: The lock cache to store the version information in.
        :param dependency: A Dependency instance.
        """
        self.resolver = resolver
        self.lock_cache_to = lock_cache_to
        self.dependency = dependency

    def resolve(self):
        """Resolve a path to a dependency.

        If we are doing an "active" resolver, meaning that waf was invoked with
        configure. Then we save the resolved checkout to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()
        self.lock_cache_to.add_dependency(dependency=self.dependency)
        return path
