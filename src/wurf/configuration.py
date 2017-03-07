#! /usr/bin/env python
# encoding: utf-8

import os

from .error import Error

class Configuration(object):

    ACTIVE = 'active'
    PASSIVE = 'passive'
    HELP = 'help'
    DEEP_FREEZE = 'deep_freeze'

    def __init__(self, project_path, args, options):
        """ Construct an instance.

        The Configuration instance is responsible for implementing the logic
        determining which actions / strategy should be executed for the
        dependency resolution.

        :param project_path: The path to the project whoms dependencies we are
           resolving as a string.
        :param args: The command-line arguments passed as a list.
        :param options: Options instance for collecing / parsing options
        """

        self.project_path = project_path
        self.args = args
        self.options = options

    def resolver_chain(self):

        if self.choose_help_chain():
            return Configuration.HELP

        elif self.choose_deep_freeze_chain():
            return Configuration.DEEP_FREEZE

        elif self.choose_active_chain():
            return Configuration.ACTIVE

        else:
            return Configuration.PASSIVE

    def choose_help_chain(self):
        """ Choose whether we should use the help resolver chain.

        There are two cases where we want to use the help chain:

        1. If we explicity pass -h or --help
        2. If we run waf without configure and we have not already configured
        """

        if '-h' in self.args or '--help' in self.args:
            return True

        if 'configure' in self.args:
            return False

        # We need some way to know if configure has been run. Since we create
        # the build folder as one of the first steps in the WafResolveContext
        # instead we check for the config.log file created by waf during
        # configuration
        config_log_path = os.path.join(self.project_path, 'build', 'config.log')

        if not os.path.isfile(config_log_path):
            # Project not yet configure - we don't have a build/config.log
            # file
            return True

        return False

    def choose_deep_freeze_chain(self):

        if not 'configure' in self.args:
            # We are not configuring
            return False

        if self.options.deep_freeze():
            # The --deep-freeze options was passed so we do not want to load
            # but rather store a deep freeze file
            return False

        deep_freeze_file = os.path.join(self.project_path,
            'deep_freeze_resolve.json')

        if not os.path.isfile(deep_freeze_file):
            # No deep freeze file exist
            return False

        # If all above checks out, we want to resolve the dependencies using the
        # deep freeze file
        return True

    def choose_active_chain(self):

        if 'configure' in self.args:
            # We are not configuring
            return True

        return False

    def write_deep_freeze(self):

        if not self.options.deep_freeze():
            return False

        if self.resolver_chain() != Configuration.ACTIVE:
            raise Error("Re-configure poject to use --deep-freeze.")

        return True
