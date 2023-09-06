#! /usr/bin/env python
# encoding: utf-8

from .error import WurfError


class VerifyFileHashResolver(object):
    def __init__(self, resolver, lock_cache, dependency):
        """Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param lock_cache: The lock cache to get the file hash from
        :param dependency: A Dependency instance.
        """
        self.resolver = resolver
        self.lock_cache = lock_cache
        self.dependency = dependency

    def resolve(self):
        """Check the file hash of the dependency and return the path.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        assert self.dependency.resolver == "http"
        assert self.dependency in self.lock_cache

        file_hash = "TODO: implement me"
        if self.lock_cache.file_hash(self.dependency) != file_hash:
            raise WurfError("Locked file hash mismatch")

        return path
