#! /usr/bin/env python
# encoding: utf-8

import json
import os

from .dependency import Dependency


class LockPathCache(object):
    # The file name of the lock file used to fix dependencies to a specific
    # verions or path
    LOCK_FILE = "lock_resolve_paths.json"

    def __init__(self, lock_cache: dict):
        self.lock_cache: dict = lock_cache

    def path(self, dependency: Dependency):
        return self.lock_cache["dependencies"][dependency.name]["path"]

    def check_sha1(self, dependency: Dependency):
        return (
            dependency.sha1 != self.lock_cache["dependencies"][dependency.name]["sha1"]
        )

    def add_path(self, dependency: Dependency, path: str):
        self.lock_cache["dependencies"][dependency.name] = {
            "sha1": dependency.sha1,
            "path": path,
        }

    def write_to_file(self, cwd: str):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockPathCache.LOCK_FILE), "w") as lock_file:
            json.dump(self.lock_cache, lock_file, indent=4, sort_keys=True)

    def __contains__(self, dependency: Dependency):
        """
        :param dependency: The Dependency instance
        :return: True if the dependency is in the cache
        """
        return dependency.name in self.lock_cache["dependencies"]

    @staticmethod
    def create_empty():
        return LockPathCache(lock_cache={"dependencies": {}})

    @staticmethod
    def create_from_file(cwd):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockPathCache.LOCK_FILE), "r") as lock_file:
            lock_cache = json.load(lock_file)

        return LockPathCache(lock_cache=lock_cache)
