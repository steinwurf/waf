#! /usr/bin/env python
# encoding: utf-8

import os

from .error import WurfError


class TryResolver(object):
    """Try to resolve."""

    def __init__(self, resolver, ctx, dependency):
        """Construct an instance.

        :param resolver: A resolver instance
        """
        assert resolver is not None
        self.resolver = resolver
        self.ctx = ctx
        self.dependency = dependency

    def resolve(self):
        """Resolve the dependency.

        :return: Path to resolved dependency as a string
        """
        try:
            path = self.resolver.resolve()
        except WurfError as e:
            # Using exc_info will attach the current exception information
            # to the log message (including traceback to where the
            # exception was thrown).
            # Waf is using the standard Python Logger so you can check the
            # docs here (read about the exc_info kwargs):
            # https://docs.python.org/2/library/logging.html
            self.ctx.logger.debug(f"Resolve failed in {self.resolver}:", exc_info=True)
            # Also write the detailed dependency info to the log
            self.ctx.logger.debug(self.dependency)

            # We also store the error message in the dependency object.
            # This will be displayed later if a TopLevelError is triggered,
            # e.g. when a dependency fails.

            # The first argument of the error contains the error message
            error_message = e.args[0]
            if not error_message.endswith("\n"):
                error_message += "\n"
            self.dependency.error_messages.append(error_message)

            return None
        except Exception:
            raise

        # The resolver did not raise an error, we check if it actually
        # produced a valid path for us.
        if path:
            assert os.path.isdir(path) or os.path.isfile(path)
        else:
            self.ctx.logger.debug(f"No path returned by {self.resolver}")
        return path
