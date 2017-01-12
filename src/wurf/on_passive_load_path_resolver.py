#! /usr/bin/env python
# encoding: utf-8

import os
import json

from .wurf_error import WurfError

class PassivePathResolverError(WurfError):
    """Exception raised by the passive resolver when in active mode."""
    def __init__(self):
        super(PassivePathResolverError, self).__init__(
            "Not loading paths from config files when in active mode.")

class OnPassiveLoadPathResolver(object):

    def __init__(self, ctx, name, sha1, active_resolve, bundle_config_path):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        :param name: Name of the dependency as a string
        :param sha1: Hash of the depenency information as a string
        :param active_resolve: True if we are in an active resolve step
        :param bundle_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        """
        self.ctx = ctx
        self.name = name
        self.sha1 = sha1
        self.active_resolve = active_resolve
        self.bundle_config_path = bundle_config_path

    def resolve(self):
        """ Resolve a path to a dependency.

        If we are doing an "passive" resolver, meaning that waf was not invoked
        with configure. Then we load the resolved path to the file-system.
        Otherwise we raise an exception.

        :return: The path as a string.
        """

        if self.active_resolve:
            raise WurfPassivePathResolverError()

        config = self.__read_config(self.name)

        if self.sha1 != config['sha1']:
            self.ctx.fatal('Failed sha1 check')

        path = str(config['path'])

        if not os.path.is_dir(path):
            self.ctx.fatal('Not valid path {}'.format(path))

        return path

    def __read_config(self):
        """ Read the dependency config from file
        """

        config_path = os.path.join(
            self.bundle_config_path, self.name + '.resolve.json')

        if not os.path.isfile(config_path):
            self.ctx.fatal('No config for {} - re-run configure'.format(
                self.name))

        with open(config_path, 'r') as config_file:
            return json.load(config_file)
