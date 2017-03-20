#! /usr/bin/env python
# encoding: utf-8

import os
import sys

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
            if os.path.realpath(link_path) == os.path.realpath(path):
                # Symlink is already in place. We may have loaded it from cache.
                self.dependency.is_symlink = True
                self.dependency.real_path = os.path.realpath(path)
                return link_path

        # os.symlink() is not available in Python 2.7 on Windows.
        # We use the original function if it is available, otherwise we
        # create a helper function for Windows
        os_symlink = getattr(os, "symlink", None)
        if not callable(os_symlink) and sys.platform == 'win32':

            def symlink_windows(target, link_path):
                # mklink is used to create an NTFS junction, i.e. symlink
                cmd = 'mklink /J "{}" "{}"'.format(
                    link_path.replace('/', '\\'), target.replace('/', '\\'))
                self.ctx.cmd_and_log(cmd)

            os_symlink = symlink_windows

        try:
            self.ctx.to_log('wurf: CreateSymlinkResolver {} -> {}'.format(
                            link_path, path))

            # We need to remove the symlink if it already exists,
            # since it may point to an incorrect folder
            if os.path.exists(link_path):
                if sys.platform == 'win32':
                    # On Windows, the symlink is not considered a link, but
                    # a directory, so it is removed with rmdir. The contents
                    # of the original folder will not be removed.
                    os.rmdir(link_path)
                else:
                    # On Unix, we remove the symlink with unlink
                    os.unlink(link_path)

            os_symlink(path, link_path)

        except Exception as e:

            # Using exc_info will attach the current exception information
            # to the log message (including the traceback)
            self.ctx.logger.debug("Symlink creation failed for: {}".format(
                self.dependency.name), exc_info=True)

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
