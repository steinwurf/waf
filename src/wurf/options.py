#! /usr/bin/env python
# encoding: utf-8

from .error import WurfError
import argparse


class Options(object):
    def __init__(
        self,
        args,
        parser,
        default_resolve_path,
        default_symlinks_path,
        supported_git_protocols,
    ):

        self.args = args
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
            "[default: '{}']".format(default_resolve_path),
        )

        self.parser.add_argument(
            "--git_protocol",
            dest="--git_protocol",
            type=non_empty_string,
            help="Use a specific git protocol to download dependencies. "
            "Supported protocols: {}".format(supported_git_protocols),
        )

        self.parser.add_argument(
            "--symlinks_path",
            dest="--symlinks_path",
            default=default_symlinks_path,
            type=non_empty_string,
            help="The folder where the dependency symlinks are placed. "
            "[default: '{}']".format(default_symlinks_path),
        )

        self.parser.add_argument(
            "--fast_resolve",
            dest="--fast_resolve",
            action="store_true",
            default=False,
            help="Load already resolved dependencies from file system. "
            "Useful for running configure without resolving dependencies "
            "again.",
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

    def fast_resolve(self):
        return self.known_args["--fast_resolve"]

    def lock_paths(self):
        return self.known_args["--lock_paths"]

    def lock_versions(self):
        return self.known_args["--lock_versions"]

    def path(self, dependency):
        return self.known_args["--%s_path" % dependency.name]

    def checkout(self, dependency):
        return self.known_args["--%s_checkout" % dependency.name]

    def __parse(self):

        known, unknown = self.parser.parse_known_args(args=self.args)

        self.known_args = vars(known)
        self.unknown_args = unknown

        if self.lock_versions() and self.lock_paths():
            raise WurfError("Incompatible options")

    def __add_path(self, dependency):

        option = "--%s_path" % dependency.name

        self.parser.add_argument(
            option,
            nargs="?",
            dest=option,
            help="Manually specify path for {}.".format(dependency.name),
        )

    def __add_checkout(self, dependency):

        option = "--%s_checkout" % dependency.name

        self.parser.add_argument(
            option,
            nargs="?",
            dest=option,
            help="Manually specify Git checkout for {}.".format(dependency.name),
        )

    def add_dependency(self, dependency):

        self.__add_path(dependency)

        if dependency.resolver == "git":

            self.__add_checkout(dependency)

        self.__parse()
