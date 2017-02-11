#! /usr/bin/env python
# encoding: utf-8

import os

from .dependency import Dependency 

class DependencyManager(object):

    def __init__(self, registry, cache, ctx, options):
        """ Construct an instance.

        As the manager resolves dependencies it will store the results
        in the dependency cache. The dependency cache contains information
        about where on the file-system a dependency is stored and allows us to
        recurse into dependencies when running other Waf commands (e.g. build,
        etc).

        The cache will have the following "layout":

            cache = {'nameX': {'recurse': True, 'path': '/tmpX'},
                     'nameY': {'recurse': False, 'path': '/tmpY'},
                     'nameZ': {'recruse': True, 'path': '/tmpZ'}}

        :param registry: A Registry instance.
        :param cache: Dict where paths to dependencies should be stored.
        :param ctx: A Waf Context instance.
        :param options: Options instance for collecing / parsing options
        """

        self.registry = registry
        self.cache = cache
        self.ctx = ctx
        self.options = options

        # Dict where we will store the dependencies already added. For
        # example two libraries may have an overlap in their
        # dependencies, causing the same dependency to be added multiple
        # times to the manager. So if we've already seen a dependency
        # we simply skip it. We do not use the self.cache dict for this purpose
        # since we want to store the full dependency information (for debugging
        # purposes).
        self.seen_dependencies = {}

    def add_dependency(self, **kwargs):
        """ Adds a dependency to the manager.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        dependency = Dependency(**kwargs)

        if self.__skip_dependency(dependency):
            return

        self.options.add_dependency(dependency)

        try:
            path = self.__resolve_dependency(dependency)
        except Exception as e:
            self.ctx.fatal("Failed resolving {} error: {}. Check logs for "
                           "more information.".format(dependency, e))

        if not path:
            return

        self.cache[dependency.name] = {'path': path, 'recurse': dependency.recurse}

        if dependency.recurse:
            self.ctx.recurse(path)

    def __skip_dependency(self, dependency):
        """ Checks if we should skip the dependency.

        :param dependency: A WurfDependency instance.
        :return: True if the dependency should be skipped, otherwise False.
        """

        if dependency.name in self.seen_dependencies:

            seen_dependency = self.seen_dependencies[dependency.name]

            if seen_dependency.sha1 != dependency.sha1:

                self.ctx.fatal(
                    "SHA1 mismatch adding dependency {} was {}".format(
                    dependency, seen_dependency))

            # This dependency is already in the seen_dependency  lets leave
            return True

        self.seen_dependencies[dependency.name] = dependency

        return False

    def __resolve_dependency(self, dependency):
        """ Gets the path to the dependency.

        :param dependency: A WurfDependency instance.
        :return: Path to where the dependency is located on the file system
            as a string. If the dependency is optional and no path was resolved
            we return None.
        """

        self.ctx.start_msg('Resolve dependency {}'.format(dependency.name))

        resolver = self.registry.require('dependency_resolver',
            dependency=dependency)

        try:

            path = resolver.resolve()

        except Exception as e:

            self.ctx.to_log('Exception while fetching dependency: {}'.format(e))

            if not dependency.optional:
                raise

            # An optional dependency might be unavailable if the user
            # does not have a license to access the repository, so we just
            # print the status message and continue
            self.ctx.end_msg('Unavailable', color='RED')

        else:
            if not os.path.isdir(path):
                self.ctx.fatal("Failed resolving {}, resolver returned non-dir"
                               " path {}".format(dependency, path))
            
            self.ctx.end_msg(path)

        return path

class HelpDependencyManager(object):

    def __init__(self, registry, cache, ctx, options):
        """ Construct an instance.

        As the manager resolves dependencies it will store the results
        in the dependency cache. The dependency cache contains information
        about where on the file-system a dependency is stored and allows us to
        recurse into dependencies when running other Waf commands (e.g. build,
        etc).

        The cache will have the following "layout":

            cache = {'nameX': {'recurse': True, 'path': '/tmpX'},
                     'nameY': {'recurse': False, 'path': '/tmpY'},
                     'nameZ': {'recruse': True, 'path': '/tmpZ'}}

        :param registry: A Registry instance.
        :param cache: Dict where paths to dependencies should be stored.
        :param ctx: A Waf Context instance.
        :param options: Options instance for collecing / parsing options
        """

        self.registry = registry
        self.cache = cache
        self.ctx = ctx
        self.options = options

        # Dict where we will store the dependencies already added. For
        # example two libraries may have an overlap in their
        # dependencies, causing the same dependency to be added multiple
        # times to the manager. So if we've already seen a dependency
        # we simply skip it. We do not use the self.cache dict for this purpose
        # since we want to store the full dependency information (for debugging
        # purposes).
        self.seen_dependencies = {}

    def add_dependency(self, **kwargs):
        """ Adds a dependency to the manager.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        dependency = Dependency(**kwargs)

        if self.__skip_dependency(dependency):
            return

        self.options.add_dependency(dependency)
            
        resolver = self.registry.require('dependency_resolver',
            dependency=dependency)
            
        path = resolver.resolve()

        if not path:
            return

        self.cache[dependency.name] = {'path': path, 'recurse': dependency.recurse}

        if dependency.recurse:
            self.ctx.recurse(path)

    def __skip_dependency(self, dependency):
        """ Checks if we should skip the dependency.

        :param dependency: A WurfDependency instance.
        :return: True if the dependency should be skipped, otherwise False.
        """

        if dependency.name in self.seen_dependencies:

            seen_dependency = self.seen_dependencies[dependency.name]

            if seen_dependency.sha1 != dependency.sha1:

                self.ctx.fatal(
                    "SHA1 mismatch adding dependency {} was {}".format(
                    dependency, seen_dependency))

            # This dependency is already in the seen_dependency  lets leave
            return True

        self.seen_dependencies[dependency.name] = dependency

        return False
