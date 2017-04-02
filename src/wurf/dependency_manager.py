#! /usr/bin/env python
# encoding: utf-8

import os
import json

from .dependency import Dependency
from .error import Error, DependencyError

class DependencyManager(object):

    def __init__(self, registry, dependency_cache, ctx, options):
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
        self.dependency_cache = dependency_cache
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

        # Actions to be executed once all dependencies have been resolved
        # will only be invoked if the post_resolve(...) fuction is invoked.
        self.post_resolve_actions = []

    def load_dependencies(self, path, mandatory=False):
        """ Loads dependencies from a resolve.json file.

        :param path: Location where resolve.json should be found.
        :param mandatory: True if the resolve.json file must exist.
        """

        resolve_path = os.path.join(path, 'resolve.json')

        if not os.path.isfile(resolve_path):

            if mandatory:
                raise Error('Mandatory resolve.json not found here: {}'.format(
                    resolve_path))
            else:
                return

        with open(resolve_path, 'r') as resolve_file:
            resolve_json = json.load(resolve_file)

        for dependency in resolve_json:
            self.add_dependency(**dependency)

    def add_dependency(self, **kwargs):
        """ Adds a dependency to the manager.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        dependency = Dependency(**kwargs)

        if self.__skip_dependency(dependency):
            return

        self.options.add_dependency(dependency)

        with self.registry.provide_value('dependency', dependency):
            resolver = self.registry.require('dependency_resolver')

        path = resolver.resolve()

        if not path:
            return

        self.dependency_cache[dependency.name] = \
            {'path': path, 'recurse': dependency.recurse}

        if dependency.recurse:
            # We do not require the 'resolve' function to be implemented in
            # dependency projects. Therefore the mandatory=False.
            #
            # str() is needed as waf does not handle unicode in its find_node
            # function (invoked from within recurse).
            self.ctx.recurse([str(path)], mandatory=False)

    def __skip_dependency(self, dependency):
        """ Checks if we should skip the dependency.

        :param dependency: A WurfDependency instance.
        :return: True if the dependency should be skipped, otherwise False.
        """
        if dependency.internal and not self.ctx.is_toplevel():
            # Internal dependencies should be skipped, if this is not the
            # top-level wscript
            return True

        if dependency.name in self.seen_dependencies:

            seen_dependency = self.seen_dependencies[dependency.name]

            if seen_dependency.sha1 != dependency.sha1:

                raise Error(
                    "SHA1 mismatch when adding:\n{}\n"
                    "the previous definition was:\n{}".format(
                    dependency, seen_dependency))

            # If the current dependency is non-optional and we have already
            # seen the same dependency as optional
            if not dependency.optional and seen_dependency.optional:
               # Store the non-optional version in seen_dependencies to
               # avoid future checks
               self.seen_dependencies[dependency.name] = dependency

               # It is not safe to skip this dependency, if there is no
               # valid path for it in the dependency_cache. In this case,
               # we should try to resolve it again as non-optional.
               if dependency.name not in self.dependency_cache:
                   return False

            # This dependency is already in the seen_dependencies
            return True

        self.seen_dependencies[dependency.name] = dependency

        return False

    def post_resolve(self):
        """ Function called when all dependencies have been resolved. """

        for action in self.post_resolve_actions:
            action(dependency_manager=self)

    def add_post_resolve_action(self, action):
        self.post_resolve_actions.append(action)
