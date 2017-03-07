#! /usr/bin/env python
# encoding: utf-8

import os
import json

class WriteDeepFreezeResolveJson(object):

    def __init__(self, project_path):
        """ Construct an instance.

        :param project_path: The path to the project as a string
        """
        self.project_path = project_path

    def __call__(self, dependency_manager):
        """ Write the paths to the dependencies
        """

        deep_freeze_path = os.path.join(
            self.project_path, 'deep_freeze_resolve.json')

        dependencies = dependency_manager.seen_dependencies

        config = {}

        for name, dependency in dependencies.items():

            path = os.path.relpath(path=dependency.real_path,
                start=self.project_path)
                
            # @todo consider chekcing the path "contained with the project"

            config[name] = {'sha1': dependency.sha1, 'path': path }

        with open(deep_freeze_path, 'w') as deep_freeze_file:
            json.dump(config, deep_freeze_file)
