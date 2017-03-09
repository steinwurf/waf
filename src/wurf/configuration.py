#! /usr/bin/env python
# encoding: utf-8

import os

from .error import Error

class Configuration(object):

    ACTIVE = 'active'
    PASSIVE = 'passive'
    HELP = 'help'
    LOCK_PATH = 'lock_path'
    LOCK_VERSION = 'lock_version'

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

        elif self.choose_lock_path_chain():
            return Configuration.LOCK_PATH

        elif self.choose_lock_version_chain():
            return Configuration.LOCK_VERSION

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

    def choose_lock_path_chain(self):

        if not 'configure' in self.args:
            # We are not configuring
            return False

        if self.options.lock_paths():
            # The --lock_paths options was passed so we do not want to load
            # but rather store locked path files
            return False

        lock_paths_dir = os.path.join(self.project_path, 'resolve_lock_paths')

        if not os.path.isdir(lock_paths_dir):
            # No lock path directory
            return False

        # If all above checks out, we want to resolve the dependencies using the
        # lock paths directory
        return True

    def choose_lock_version_chain(self):

        if not 'configure' in self.args:
            # We are not configuring
            return False

        if self.options.lock_versions():
            # The --lock_versions options was passed so we do not want to load
            # but rather store locked version files
            return False

        lock_versions_dir = os.path.join(self.project_path,
            'resolve_lock_versions')

        if not os.path.isdir(lock_versions_dir):
            # No lock versions directory
            return False

        # If all above checks out, we want to resolve the dependencies using the
        # lock verions directory
        return True

    def choose_active_chain(self):

        if 'configure' in self.args:
            # We are not configuring
            return True

        return False

    def write_lock_paths(self):

        if not self.options.lock_paths():
            return False

        if self.resolver_chain() != Configuration.ACTIVE:
            raise Error("Re-configure poject to use --lock_paths.")

        return True

    def write_lock_versions(self):

        if not self.options.lock_versions():
            return False

        if self.resolver_chain() != Configuration.ACTIVE:
            raise Error("Re-configure poject to use --lock_versions.")

        return True
