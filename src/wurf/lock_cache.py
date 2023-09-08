#! /usr/bin/env python
# encoding: utf-8

import json
import hashlib
import os

from .error import WurfError


class LockCache(object):
    def __init__(self, lock_cache):
        self.lock_cache = lock_cache

    def type(self):
        return self.lock_cache["type"]

    def path(self, dependency):
        return self.lock_cache["dependencies"][dependency.name]["path"]

    def checkout(self, dependency):
        assert dependency.resolver == "git"
        return self.lock_cache["dependencies"][dependency.name]["checkout"]

    def check_sha1(self, dependency):
        lock_sha1 = self.lock_cache["dependencies"][dependency.name]["sha1"]
        return dependency.sha1 != lock_sha1

    def write_to_file(self, lock_path):
        with open(lock_path, "w") as lock_file:
            json.dump(self.lock_cache, lock_file, indent=4, sort_keys=True)

    def add_path(self, dependency, path):
        self.lock_cache["dependencies"][dependency.name] = {
            "sha1": dependency.sha1,
            "path": path,
        }

    def add_checkout(self, dependency, checkout):
        self.lock_cache["dependencies"][dependency.name] = {
            "sha1": dependency.sha1,
            "checkout": checkout,
        }

    def add_file(self, dependency, path):
        self.lock_cache["dependencies"][dependency.name] = {
            "sha1": dependency.sha1,
            "file_hash": self.__calculate_file_hash(path),
        }

    def check_file_hash(self, dependency, path):
        assert dependency.resolver == "http"
        lock_file_hash = self.lock_cache["dependencies"][dependency.name]["file_hash"]
        return lock_file_hash != self.__calculate_file_hash(path)

    def __calculate_file_hash(self, path):
        assert os.path.exists(path)
        sha1 = hashlib.sha1()
        if os.path.isfile(path):
            sha1.update(open(path, "rb").read())
        elif os.path.isdir(path):
            # Calculate the hash of all files in the directory
            for root, _, files in os.walk(path):
                for file in files:
                    f = os.path.join(root, file)
                    sha1.update(open(f, "rb").read())
        else:
            raise WurfError(f"Unknown file type: {path}")
        return sha1.hexdigest()

    def __contains__(self, dependency):
        """
        :param dependency: The Dependency instance
        :return: True if the dependency is in the cache
        """
        return dependency.name in self.lock_cache["dependencies"]

    @staticmethod
    def create_empty(options):
        if options.lock_versions():
            lock_cache = {"type": "versions", "dependencies": {}}

            return LockCache(lock_cache=lock_cache)

        elif options.lock_paths():
            lock_cache = {"type": "paths", "dependencies": {}}

            return LockCache(lock_cache=lock_cache)
        else:
            raise WurfError("Store lock cache requested, with unknown lock type.")

    @staticmethod
    def create_from_file(lock_path):
        with open(lock_path, "r") as lock_file:
            lock_cache = json.load(lock_file)

        return LockCache(lock_cache=lock_cache)
