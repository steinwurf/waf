#! /usr/bin/env python
# encoding: utf-8

import os

from .error import Error

class TryResolver(object):
    """ Try to resolve."""

    def __init__(self, resolver, ctx):
        """ Construct an instance.

        :param resolver: A resolver instance
        """
        self.resolver = resolver
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        try:
            path = self.resolver.resolve()
        except Error as e:
            # Using exc_info will attach the current exception information
            # to the log message (including traceback to where the
            # exception was thrown).
            # Waf is using the standard Python Logger so you can check the
            # docs here (read about the exc_info kwargs):
            # https://docs.python.org/2/library/logging.html
            self.ctx.logger.debug("Resolve failed in {}:".format(
                self.resolver), exc_info=True)

            return None
        except:
            raise

        # The resolver did not raise an error, we check if it actually
        # produced a valid path for us.
        if path:
            assert os.path.isdir(path)
        else:
            self.ctx.logger.debug(
                "No path returned by {}".format(self.resolver))
        return path
