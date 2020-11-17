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
        """ Construct a new CreateSymlinkResolver instance.

        :param resolver: The resolver used to fecth the dependency
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
            return path

        link_path = os.path.join(self.symlinks_path, self.dependency.name)

        if os.path.exists(link_path):
            # On Windows, os.path.realpath does not follow the symlink,
            # therefore the two sides are only equal if link_path == path
            if os.path.realpath(link_path) == os.path.realpath(path):
                # Symlink is already in place.
                # We may have loaded it from cache.
                self.dependency.is_symlink = True
                self.dependency.real_path = os.path.realpath(path)
                return link_path

        try:

            self.ctx.to_log('wurf: CreateSymlinkResolver {} -> {}'.format(
                            link_path, path))

            try:
                # We set overwrite True since We need to remove the symlink if it
                # already exists since it may point to an incorrect folder
                create_symlink(from_path=path, to_path=link_path,
                               overwrite=True, relative=True)

            except RelativeSymlinkError:

                self.ctx.to_log('wurf: Using relative symlink failed - fallback '
                                'to absolute.')

                create_symlink(from_path=path, to_path=link_path,
                               overwrite=True, relative=False)

        except Exception as ex:

            msg = "Symlink creation failed for: {}\n".format(
                self.dependency.name)

            # We also want to log the captured output if the command failed
            # with a CalledProcessError, the output would be lost otherwise
            if hasattr(ex, 'output'):
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
