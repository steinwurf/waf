#! /usr/bin/env python
# encoding: utf-8

import os


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
    # 5. The "store_from_lock" will load the dependency information from the
    #    lock file and fetch dependencies.
    RESOLVE = "resolve"
    LOAD = "load"
    HELP = "help"
    RESOLVE_AND_LOCK = "resolve_and_lock"
    RESOLVE_FROM_LOCK = "resolve_from_lock"

    # The file name of the lock file used to fix dependencies to a specific
    # verions or path
    LOCK_FILE = "lock_resolve.json"

    def __init__(self, project_path, args, options, waf_lock_file):
        """Construct an instance.

        The Configuration instance is responsible for implementing the logic
        determining which actions / strategy should be executed for the
        dependency resolution.

        :param project_path: The path to the project whose dependencies we are
            resolving as a string.
        :param args: The command-line arguments passed as a list.
        :param options: Options instance for collecting / parsing options
        :param waf_lock_file: The lock file created by waf after a successful
            configure.
        """
        self.project_path = project_path
        self.args = args
        self.options = options
        self.waf_lock_file = waf_lock_file

    def resolver_chain(self):

        if self.choose_help():
            return Configuration.HELP

        elif self.choose_resolve_and_lock():
            return Configuration.RESOLVE_AND_LOCK

        elif self.choose_resolve_from_lock():
            return Configuration.RESOLVE_FROM_LOCK

        elif self.choose_resolve():
            return Configuration.RESOLVE

        else:
            return Configuration.LOAD

    def choose_help(self):
        """Choose whether we should use the help resolver chain.

        There are two cases where we want to use the help chain:

        1. If we explicitly pass -h or --help
        2. If we run waf without wanting to resolve
        """

        if "-h" in self.args or "--help" in self.args:
            return True

        if self.choose_resolve():
            return False

        # We use the lock file created by waf to check if the project
        # has been already configured
        waf_lock_path = os.path.join(self.project_path, self.waf_lock_file)

        if not os.path.isfile(waf_lock_path):
            # Project not yet configured
            return True

        return False

    def choose_resolve_from_lock(self):

        if "configure" not in self.args:
            # We are not configuring
            return False

        # We are not configuring, check for lock file
        lock_file = os.path.join(self.project_path, "lock_resolve.json")

        if not os.path.isfile(lock_file):
            # No lock file
            return False

        # If all above checks out, we want to resolve the dependencies using
        # the lock file
        return True

    def choose_resolve_and_lock(self):

        if "configure" not in self.args:
            # We are not configuring
            return False

        # We are configuring
        if self.options.lock_paths() or self.options.lock_versions():
            # One of the lock options were passed, so we want to write the lock
            # file rather than use it.
            return True

        return False

    def choose_resolve(self):

        for command in ["configure", "resolve"]:
            if command in self.args:
                # We should resolve
                return True

        return False
