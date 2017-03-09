#! /usr/bin/env python
# encoding: utf-8

import os
import json
import shutil

from .error import Error

class StoreLockPathResolver(object):

    def __init__(self, resolver, dependency, project_path):
        """ Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param dependency: A Dependency instance.
        :param project_path: The path to the project as a string
        """
        self.resolver = resolver
        self.dependency = dependency
        self.project_path = project_path

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "active" resolver, meaning that waf was invoked with
        configure. Then we save the resolved path to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        self.__check_path(path=path)
        self.__write_config(path=path)

        return path

    def __check_path(self, path):

        child = os.path.realpath(path)
        parent = os.path.realpath(self.project_path)

        if not child.startswith(parent):
            raise Error("Locked paths must be a within parent project")

    def __write_config(self, path):
        """ Write the dependency config to file

        :param path: The path to the dependency as a string.
        """

        config_path = os.path.join(self.project_path, 'resolve_lock_paths',
            self.dependency.name + '.lock_path.json')

        if self.dependency.is_symlink:
            path = self.dependency.real_path

        config = {'sha1': self.dependency.sha1, 'path': path }

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)

    @staticmethod
    def prepare_directory(project_path):
        """ Prepare the resolve_lock_paths directory.

        If it already exists remove the content in it.
        """

        lock_paths = os.path.join(project_path, 'resolve_lock_paths')

        if os.path.isdir(lock_paths):
            shutil.rmtree(lock_paths)

        os.makedirs(lock_paths)
