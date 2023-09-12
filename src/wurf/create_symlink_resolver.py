#! /usr/bin/env python
# encoding: utf-8

import os

from .symlink import create_symlink
from .error import RelativeSymlinkError


class CreateSymlinkResolver(object):
    """
    Creates a local symlink for a resolved dependency.
    """

    def __init__(self, resolver, dependency, symlinks_path, ctx):
        """Construct a new CreateSymlinkResolver instance.

        :param resolver: The resolver used to fetch the dependency
        :param dependency: The Dependency object.
        :param symlinks_path: The folder where the symlink should be created.
        :param ctx: A Waf Context instance.
        """
        self.resolver = resolver
        self.dependency = dependency
        self.symlinks_path = symlinks_path
        self.ctx = ctx

        assert os.path.isabs(self.symlinks_path)

    def resolve(self):
        """
        Creates a local symlink to the resolved dependency.

        :return: The path to the newly created symlink.
        """
        path = self.resolver.resolve()

        if not path:
            # If no path was returned skip symlink generation
            return path

        if self.dependency.is_symlink:
            # If the path returned is already a symlink, this is the case if the
            # dependency is loaded from cache e.g. with fast-resolve. In this
            # case the symlink resolve should use the real path as the target
            # for the symlink
            path = self.dependency.real_path

        link_path = os.path.join(self.symlinks_path, self.dependency.name)

        try:
            self.ctx.to_log(f"wurf: CreateSymlinkResolver {link_path} -> {path}")

            try:
                # We set overwrite True since We need to remove the symlink if it
                # already exists since it may point to an incorrect folder
                create_symlink(
                    from_path=path, to_path=link_path, overwrite=True, relative=True
                )

            except RelativeSymlinkError:
                self.ctx.to_log(
                    "wurf: Using relative symlink failed - fallback to absolute."
                )

                create_symlink(
                    from_path=path, to_path=link_path, overwrite=True, relative=False
                )

        except Exception as ex:
            msg = f"Symlink creation failed for: {self.dependency.name}\n"

            # We also want to log the captured output if the command failed
            # with a CalledProcessError, the output would be lost otherwise
            if hasattr(ex, "output"):
                msg += str(ex.output)

            # Using exc_info will attach the current exception information
            # to the log message (including the traceback)
            self.ctx.logger.debug(msg, exc_info=True)

            # Return the original path if something went wrong
            return path

        self.dependency.is_symlink = True
        self.dependency.real_path = path

        # Return the path to the new symlink
        return link_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
