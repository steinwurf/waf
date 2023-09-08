#! /usr/bin/env python
# encoding: utf-8

import json
import hashlib
import os

from .error import WurfError


class LockCache(object):
    # The file name of the lock file used to fix dependencies to a specific
    # verions or path
    LOCK_FILE = "lock_resolve.json"

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
        return (
            dependency.sha1 != self.lock_cache["dependencies"][dependency.name]["sha1"]
        )

    def check_content(self, dependency):
        if self.type() == "paths":
            return False
        if dependency.resolver == "git":
            checkout = self.checkout(dependency)
            if "git_tag" in dependency:
                return checkout != dependency.git_tag
            elif "git_commit" in dependency:
                return checkout != dependency.git_commit
            else:
                raise WurfError("Not stable checkout information found.")
        elif dependency.resolver == "http":
            assert hasattr(
                dependency, "real_path"
            ), "Dependency must have a real_path attribute"
            return (
                self.__calculate_file_hash(dependency.real_path)
                != self.lock_cache["dependencies"][dependency.name]["file_hash"]
            )

    def add_dependency(self, dependency):
        if dependency.resolver == "git":
            checkout = None

            if dependency.git_tag:
                checkout = dependency.git_tag
            elif dependency.git_commit:
                checkout = dependency.git_commit
            else:
                raise WurfError("Not stable checkout information found.")

            self.lock_cache["dependencies"][dependency.name] = {
                "sha1": dependency.sha1,
                "checkout": checkout,
            }
        elif dependency.resolver == "http":
            assert hasattr(
                dependency, "real_path"
            ), "Dependency must have a real_path attribute"

            self.lock_cache["dependencies"][dependency.name] = {
                "sha1": dependency.sha1,
                "file_hash": self.__calculate_file_hash(dependency.real_path),
            }

    def write_to_file(self, cwd):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockCache.LOCK_FILE), "w") as lock_file:
            json.dump(self.lock_cache, lock_file, indent=4, sort_keys=True)

    def add_path(self, dependency, path):
        self.lock_cache["dependencies"][dependency.name] = {
            "sha1": dependency.sha1,
            "path": path,
        }

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
    def create_from_file(cwd):
        assert os.path.exists(cwd)
        with open(os.path.join(cwd, LockCache.LOCK_FILE), "r") as lock_file:
            lock_cache = json.load(lock_file)

        return LockCache(lock_cache=lock_cache)
