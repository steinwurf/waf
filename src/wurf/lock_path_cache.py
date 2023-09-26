#! /usr/bin/env python
# encoding: utf-8

import json
import os

from .dependency import Dependency


class LockPathCache(object):
    # The file name of the lock file used to fix dependencies to a specific
    # verions or path
    LOCK_FILE = "lock_path_resolve.json"

    def __init__(self, cache: dict):
        self.cache: dict = cache

    def path(self, dependency: Dependency):
        return self.cache[dependency.name]["path"]

    def check_sha1(self, dependency: Dependency):
        return dependency.sha1 != self.cache[dependency.name]["sha1"]

    def check_content(self, **kwargs):
        return False

    def resolver_info(self, **kwargs):
        return None

    def add_path(self, dependency: Dependency, path: str):
        self.cache[dependency.name] = {
            "sha1": dependency.sha1,
            "path": path,
        }

    def write_to_file(self, cwd: str):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockPathCache.LOCK_FILE), "w") as lock_file:
            json.dump(self.cache, lock_file, indent=4, sort_keys=True)

    def __contains__(self, dependency: Dependency):
        """
        :param dependency: The Dependency instance
        :return: True if the dependency is in the cache
        """
        return dependency.name in self.cache

    @staticmethod
    def create_empty():
        return LockPathCache(cache={})

    @staticmethod
    def create_from_file(cwd: str):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockPathCache.LOCK_FILE), "r") as lock_file:
            cache = json.load(lock_file)

        return LockPathCache(cache=cache)
