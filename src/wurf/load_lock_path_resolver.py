#! /usr/bin/env python
# encoding: utf-8

import os
import json

from .error import DependencyError


class LoadLockPathResolver(object):
    def __init__(self, dependency, project_path):
        """Construct an instance.

        :param project_path: The path to the project as a string
        """
        self.dependency = dependency
        self.project_path = project_path

    def resolve(self):
        """Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """

        config = self.__read_config()

        if self.dependency.sha1 != config["sha1"]:
            raise DependencyError("Failed sha1 check", self.dependency)

        path = str(config["path"])

        if not os.path.isdir(path):
            raise DependencyError(f'Invalid path: "{path}"', self.dependency)

        return path

    def __read_config(self):
        """Read the dependency config from file"""

        config_path = os.path.join(
            self.project_path,
            "resolve_lock_paths",
            self.dependency.name + ".lock_path.json",
        )

        if not os.path.isfile(config_path):
            raise DependencyError(
                "No lock_path - re-run configure with --lock_paths", self.dependency
            )

        with open(config_path, "r") as config_file:
            return json.load(config_file)
