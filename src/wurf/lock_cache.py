#! /usr/bin/env python
# encoding: utf-8

import json

from .error import WurfError, DependencyError


class LockCache(object):

    def __init__(self, lock_cache):
        self.lock_cache = lock_cache

    def type(self):
        return self.lock_cache['type']

    def path(self, dependency):
        return self.lock_cache['dependencies'][dependency.name]['path']

    def checkout(self, dependency):
        return self.lock_cache['dependencies'][dependency.name]['checkout']

    def check_sha1(self, dependency):

        lock_sha1 = self.lock_cache['dependencies'][dependency.name]['sha1']

        if dependency.sha1 != lock_sha1:
            raise DependencyError(
                msg="SHA1 mismatch. Locked SHA1: {}".format(lock_sha1),
                dependency=dependency)

    def write_to_file(self, lock_path):
        with open(lock_path, 'w') as lock_file:
            json.dump(self.lock_cache, lock_file, indent=4, sort_keys=True)

    def add_path(self, dependency, path):
        self.lock_cache['dependencies'][dependency.name] = {
            'sha1': dependency.sha1, 'path': path}

    def add_checkout(self, dependency, checkout):
        self.lock_cache['dependencies'][dependency.name] = {
            'sha1': dependency.sha1, 'checkout': checkout}

    def __contains__(self, dependency):
        """
        :param dependency: The Dependency instance
        :return: True if the dependency is in the cache
        """
        return dependency.name in self.lock_cache['dependencies']

    @staticmethod
    def create_empty(options):
        if options.lock_versions():
            lock_cache = {'type': 'versions', 'dependencies': {}}

            return LockCache(lock_cache=lock_cache)

        elif options.lock_paths():
            lock_cache = {'type': 'paths', 'dependencies': {}}

            return LockCache(lock_cache=lock_cache)
        else:
            raise WurfError('Store lock cache requested, with unknown lock type.')

    @staticmethod
    def create_from_file(lock_path):
        with open(lock_path, 'r') as lock_file:
            lock_cache = json.load(lock_file)

        return LockCache(lock_cache=lock_cache)
