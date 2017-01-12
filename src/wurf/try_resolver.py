#! /usr/bin/env python
# encoding: utf-8

import argparse
import sys
import os


#           +--------------------------+
#           |   WurfHashDependency     |
#           |                          |
#           |   - Hash the dependency  |
#           |     using sha1.          |
#           +--------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#      +-----------------------------------+
#      |   WurfDependencyCache             |
#      |                                   |
#      |   - Cache the path and sha1 for   |
#      |     a resolved dependency.        |
#      |   - Store the path and sha1 in a  |
#      |     persistant cache file.        |
#      |   - Checks that if a dependency   |
#      |     is added twice their sha1     |
#      |     must match.                   |
#      |                                   |
#      +-----------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#     +------------------------------------+
#     |  WurfUserResolve                   |
#     |                                    |
#     |  - Check if user specified a path  |
#     |    on the command-line.            |
#     |                                    |
#     +------------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#    +----------------------------------------+
#    |  WurfFastResolve                       |
#    |                                        |
#    |  - Active if the --fast-resolve option |
#    |    is specified.                       |
#    |  - If the cache file exists            |
#    |    loads the path from there.          |
#    |                                        |
#    +----------------------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#       +---------------------------------+
#       |  WurfResolve                    |
#       |                                 |
#       |  - Uses the specified resolver  |
#       |    type to fetch the dependency |
#       +---------------------------------+






from . import wurf_error

class NoPathResolvedError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self):
        super(NoPathResolvedError, self).__init__(
            "Could not resolve dependency path.")


class TryResolver(object):
    """ Iterates through a list of resolvers until a path is resolved."""

    def __init__(self, resolvers, ctx):
        """ Construct an instance.

        :param resolvers: A list of resolvers object for the available
           sources
        :param ctx: A Waf Context instance.
        """
        self.resolvers = resolvers
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        :raises NoPathResolved: if no resolver produced a valid path. 
        """

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
            else:
                
                assert os.path.isdir(path)
                return path
        else:
            raise NoPathResolvedError()
