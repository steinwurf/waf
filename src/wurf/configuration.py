#! /usr/bin/env python
# encoding: utf-8

import os
from .lock_path_cache import LockPathCache
from .lock_version_cache import LockVersionCache
from .sub_command import UpgradeSubCommand


class Configuration(object):
    # These are the main resolver chains/configurations:
    #
    # 1. The "resolve" chain: This chain goes to the network and fetches stuff
    # 2. The "load" or chain: This chain will load information
    #    from the file system.
    # 3. The "help" chain: This chain tries to interate though as many
    #    dependencies as possible to get all options.
    # 4. The "resolve_lock" works like "resolve", but also write a lock file
    #    to the project directory - fixating a dependency to a specific
    #    version or path
    # 5. The "resolve_from_lock" will load the dependency information from the
    #    lock file and fetch dependencies.
    RESOLVE = "resolve"
    LOAD = "load"
    HELP = "help"
    RESOLVE_FROM_PATH_LOCK = "resolve_from_path_lock"
    RESOLVE_FROM_VERSION_LOCK = "resolve_from_version_lock"

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

        elif self.choose_resolve_from_lock(LockPathCache.LOCK_FILE):
            return Configuration.RESOLVE_FROM_PATH_LOCK

        elif self.choose_resolve_from_lock(LockVersionCache.LOCK_FILE):
            return Configuration.RESOLVE_FROM_VERSION_LOCK

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

    def lock_paths(self):
        # Lock paths if configuring and the lock paths option was passed
        if "configure" in self.args and self.options.lock_paths():
            return True
        elif "resolve" in self.args and self.options.lock_paths():
            return True
        return False

    def lock_versions(self):
        # An upgrade rewrites the lock file, but never creates one
        if self.upgrading() and self.choose_resolve_from_lock(
            LockVersionCache.LOCK_FILE
        ):
            return True
        # Lock versions if configuring and the lock versions option was passed
        if "configure" in self.args and self.options.lock_versions():
            return True
        elif "resolve" in self.args and self.options.lock_versions():
            return True
        return False

    def upgrade(self):
        """Return the dependencies to upgrade.

        :return: None if we are not upgrading, otherwise the dependency names
            as a list. An empty list means that all dependencies should be
            upgraded.
        """
        if self.choose_help():
            return None

        sub_command = self.options.sub_command()

        if not isinstance(sub_command, UpgradeSubCommand):
            return None

        return sub_command.arguments

    def upgrading(self):
        """:return: True if dependencies should be upgraded."""
        return self.upgrade() is not None

    def choose_resolve_from_lock(self, lock_file):
        if not self.choose_resolve():
            # We are not configuring or resolving
            return False

        # Check for lock file
        return os.path.exists(os.path.join(self.project_path, lock_file))

    def choose_resolve(self):
        return any([c in self.args for c in ["configure", "resolve"]])
