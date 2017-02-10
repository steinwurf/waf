#! /usr/bin/env python
# encoding: utf-8

import argparse
import sys
import os

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
        last_exception = None

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as ex:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
                last_exception = ex
            else:

                assert os.path.isdir(path)
                return path

        if last_exception:
            raise last_exception
        else:
            raise NoPathResolvedError()
