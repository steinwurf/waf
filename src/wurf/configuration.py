#! /usr/bin/env python
# encoding: utf-8

import os

from .error import Error

class Configuration(object):

    # These are the main resolver chains/configurations:
    #
    # 1. The "store" chain: This chain goes to the network and fetches stuff
    # 2. The "load" or chain: This chain will load information
    #    from the file system.
    # 3. The "help" chain: This chain tries to interate though as many
    #    dependencies as possible to get all options.
    # 4. The "store_lock" works like "store", but also write a lock file
    #    to the project directory - fixating a dependency to a specific
    #    version or path
    # 5. The "store_from_lock" will load the depenency information from the lock
    #    file and fetch dependencies.
    STORE = 'store'
    LOAD = 'load'
    HELP = 'help'
    STORE_LOCK = 'store_lock'
    STORE_FROM_LOCK = 'store_from_lock'

    # The file name of the lock file used to fix dependencies to a specific
    # verions or path
    LOCK_FILE = 'lock_resolve.json'

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

        if self.choose_help():
            return Configuration.HELP

        elif self.choose_store_lock():
            return Configuration.STORE_LOCK

        elif self.choose_store_from_lock():
            return Configuration.STORE_FROM_LOCK

        elif self.choose_store():
            return Configuration.STORE

        else:
            return Configuration.LOAD

    def choose_help(self):
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

    def choose_store_from_lock(self):

        if not 'configure' in self.args:
            # We are not configuring
            return False

        # We are not configuring, check for lock file
        lock_file = os.path.join(self.project_path, 'lock_resolve.json')

        if not os.path.isfile(lock_file):
            # No lock file
            return False

        # If all above checks out, we want to resolve the dependencies using the
        # lock file
        return True

    def choose_store_lock(self):

        if not 'configure' in self.args:
            # We are not configuring
            return False

        # We are configuring
        if self.options.lock_paths() or self.options.lock_versions():
            # One of the lock options were passed, so we want to write the lock
            # file rather than use it.
            return True

        return False

    def choose_store(self):

        if 'configure' in self.args:
            # We are not configuring
            return True

        return False
