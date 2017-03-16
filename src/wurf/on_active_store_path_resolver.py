#! /usr/bin/env python
# encoding: utf-8

import os
import json

class OnActiveStorePathResolver(object):

    def __init__(self, resolver, dependency, resolve_config_path):
        """ Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param dependency: A Dependency instance.
        :param resolve_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        """
        self.resolver = resolver
        self.dependency = dependency
        self.resolve_config_path = resolve_config_path

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "active" resolver, meaning that waf was invoked with
        configure. Then we save the resolved path to the file-system.

        :return: The path as a string.
        """

        path = self.resolver.resolve()

        self.__write_config(path=path)

        return path

    def __write_config(self, path):
        """ Write the dependency config to file

        :param path: The path to the dependency as a string.
        """

        config_path = os.path.join(
            self.resolve_config_path, self.dependency.name + '.resolve.json')

        config = {'sha1': self.dependency.sha1, 'path': path,
            'is_symlink': self.dependency.is_symlink,
            'real_path': self.dependency.real_path }

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)
