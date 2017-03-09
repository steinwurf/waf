#! /usr/bin/env python
# encoding: utf-8

import os
import json
import shutil

from .error import Error

class StoreLockVersionResolver(object):

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
        configure. Then we save the resolved checkout to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        self.__write_config(path=path)

        return path

    def __write_config(self, path):
        """ Write the dependency config to file

        :param path: The path to the dependency as a string.
        """

        config_path = os.path.join(self.project_path, 'resolve_lock_versions',
            self.dependency.name + '.lock_version.json')

        checkout = None

        if self.dependency.git_tag:
            checkout = self.dependency.git_tag
        elif self.dependency.git_commit:
            checkout = self.dependency.git_commit
        else:
            raise Error('Not stable checkout information found.')

        config = {'sha1': self.dependency.sha1, 'checkout': checkout }

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)

    @staticmethod
    def prepare_directory(project_path):
        """ Prepare the resolve_lock_versions directory.

        If it already exists remove the content in it.
        """

        lock_versions = os.path.join(project_path, 'resolve_lock_versions')

        if os.path.isdir(lock_versions):
            shutil.rmtree(lock_versions)

        os.makedirs(lock_versions)
