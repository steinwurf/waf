#! /usr/bin/env python
# encoding: utf-8

import os

from .error import WurfError


class StoreLockPathResolver(object):
    def __init__(self, resolver, lock_cache, project_path, dependency):
        """Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param lock_cache: The lock cache to store the version information in.
        :param project_path: The path to the project who's dependencies we are
           resolving as a string.
        :param dependency: A Dependency instance.
        """
        self.resolver = resolver
        self.lock_cache = lock_cache
        self.project_path = project_path
        self.dependency = dependency

    def resolve(self):
        """Resolve a path to a dependency.

        If we are doing an "active" resolver, meaning that waf was invoked with
        configure. Then we save the resolved path to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        self.__check_path(path=path)

        if self.dependency.is_symlink:
            lock_path = self.dependency.real_path
        else:
            lock_path = path

        lock_path = os.path.relpath(path=lock_path, start=self.project_path)

        self.lock_cache.add_path(dependency=self.dependency, path=lock_path)

        return path

    def __check_path(self, path):

        child = os.path.realpath(path)
        parent = os.path.realpath(self.project_path)

        if not child.startswith(parent):
            raise WurfError("Locked paths must be a within parent project")
