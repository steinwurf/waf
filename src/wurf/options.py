#! /usr/bin/env python
# encoding: utf-8

from .error import WurfError
import argparse


class Options(object):
    # The command running the dependency resolution
    RESOLVE_COMMAND = "resolve"

    # The sub command upgrading dependencies, used as
    # "resolve upgrade [dependency ...]"
    UPGRADE_COMMAND = "upgrade"

    def __init__(
        self,
        args,
        parser,
        default_resolve_path,
        default_symlinks_path,
        supported_git_protocols,
    ):
        # The dependencies to upgrade (None if we are not upgrading) and the
        # remaining command-line arguments
        self.upgrade_dependencies, self.args = Options.extract_upgrade(args)

        self.parser = parser

        self.known_args = {}
        self.unknown_args = []

        def non_empty_string(value):
            if not value:
                raise argparse.ArgumentTypeError("Empty string is not allowed.")
            return value

        self.parser.add_argument(
            "--resolve_path",
            dest="--resolve_path",
            default=default_resolve_path,
            type=non_empty_string,
            help="The folder where the resolved dependencies are downloaded. "
            f"[default: '{default_resolve_path}']",
        )

        self.parser.add_argument(
            "--git_protocol",
            dest="--git_protocol",
            type=non_empty_string,
            help="Use a specific git protocol to download dependencies. "
            f"Supported protocols: {supported_git_protocols}",
        )

        self.parser.add_argument(
            "--symlinks_path",
            dest="--symlinks_path",
            default=default_symlinks_path,
            type=non_empty_string,
            help="The folder where the dependency symlinks are placed. "
            f"[default: '{default_symlinks_path}']",
        )

        self.parser.add_argument(
            "--lock_paths",
            dest="--lock_paths",
            action="store_true",
            default=False,
            help="Creates the resolve_lock_paths directory which contains the "
            "paths to all resolved dependencies.",
        )

        self.parser.add_argument(
            "--lock_versions",
            dest="--lock_versions",
            action="store_true",
            default=False,
            help="Creates the resolve_lock_versions directory which contains "
            "the specific versions of all resolved dependencies.",
        )

        self.__parse()

    def resolve_path(self):
        return self.known_args["--resolve_path"]

    def symlinks_path(self):
        return self.known_args["--symlinks_path"]

    def git_protocol(self):
        return self.known_args["--git_protocol"]

    def lock_paths(self):
        return self.known_args["--lock_paths"]

    def lock_versions(self):
        return self.known_args["--lock_versions"]

    def upgrade(self):
        """Return the dependencies to upgrade.

        :return: None if the upgrade sub command was not used, otherwise the
            dependency names as a list. An empty list means that all
            dependencies should be upgraded.
        """
        return self.upgrade_dependencies

    def path(self, dependency):
        return self.known_args[f"--{dependency.name}_path"]

    def checkout(self, dependency):
        return self.known_args[f"--{dependency.name}_checkout"]

    def __parse(self):
        known, unknown = self.parser.parse_known_args(args=self.args)

        self.known_args = vars(known)
        self.unknown_args = unknown

        if self.lock_versions() and self.lock_paths():
            raise WurfError("Incompatible options")

        if (
            self.lock_versions() or self.lock_paths()
        ) and "--skip_internal" in self.args:
            raise WurfError("Incompatible options")

        if self.upgrade() is not None and "--skip_internal" in self.args:
            raise WurfError("Incompatible options")

    @staticmethod
    def extract_upgrade(args):
        """Take the upgrade sub command out of the command-line arguments.

        Waf treats every argument which is not an option as a command, so the
        sub command and the dependency names must be removed before waf parses
        the arguments.

        :param args: The command-line arguments as a list
        :return: A (dependencies, arguments) tuple, where dependencies is None
            if the sub command was not used and arguments are the remaining
            command-line arguments.
        """
        for index, arg in enumerate(args):
            if arg != Options.RESOLVE_COMMAND:
                continue

            command = index + 1

            if command >= len(args) or args[command] != Options.UPGRADE_COMMAND:
                continue

            # The dependency names follow the sub command and stop at the
            # first option
            start = command + 1
            end = start

            while end < len(args) and not args[end].startswith("-"):
                end += 1

            return args[start:end], args[:command] + args[end:]

        return None, args

    def __add_path(self, dependency):
        option = f"--{dependency.name}_path"

        self.parser.add_argument(
            option,
            nargs="?",
            dest=option,
            help=f"Manually specify path for {dependency.name}.",
        )

    def __add_checkout(self, dependency):
        option = f"--{dependency.name}_checkout"

        self.parser.add_argument(
            option,
            nargs="?",
            dest=option,
            help=f"Manually specify Git checkout for {dependency.name}.",
        )

    def add_dependency(self, dependency):
        self.__add_path(dependency)

        if dependency.resolver == "git":
            self.__add_checkout(dependency)

        self.__parse()
