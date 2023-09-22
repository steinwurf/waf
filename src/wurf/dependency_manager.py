#! /usr/bin/env python
# encoding: utf-8

import os
import json

from .dependency import Dependency
from .error import WurfError
from .lock_version_cache import LockVersionCache


class DependencyManager(object):
    RESOLVE_FILE = "resolve.json"

    def __init__(self, registry, dependency_cache, ctx, git, options, skip_internal):
        """Construct an instance.

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
        :param options: Options instance for collecting / parsing options
        """

        self.registry = registry
        self.dependency_cache = dependency_cache
        self.ctx = ctx
        self.git = git
        self.options = options
        self.skip_internal = skip_internal

        # Dict where we will store the dependencies already added. For
        # example two libraries may have an overlap in their
        # dependencies, causing the same dependency to be added multiple
        # times to the manager. So if we've already seen a dependency
        # we simply skip it. We do not use the self.cache dict for this purpose
        # since we want to store the full dependency information (for debugging
        # purposes).
        self.seen_dependencies = {}

        # Actions to be executed once all dependencies have been resolved
        # will only be invoked if the post_resolve(...) function is invoked.
        self.post_resolve_actions = []

        # Set of optional dependencies that have been marked as enabled
        self.enabled_dependencies = set()

        # Dict where we store the locked versions of dependencies
        self.locked_versions = {}

    def load_dependencies(self, path):
        """Loads dependencies from a resolve.json file.

        :param path: Location where resolve.json should be found.
        :param mandatory: True if the resolve.json file must exist.
        """

        resolve_json_path = os.path.join(path, DependencyManager.RESOLVE_FILE)
        if not os.path.isfile(resolve_json_path):
            return

        with open(resolve_json_path, "r") as resolve_file:
            resolve_json = json.load(resolve_file)

        locked_versions = {}
        resolve_lock_path = os.path.join(path, LockVersionCache.LOCK_FILE)
        if os.path.isfile(resolve_lock_path):
            with open(resolve_lock_path, "r") as f:
                locked_versions = json.load(f)

        for dependency in resolve_json:
            locked_version = locked_versions.get(dependency["name"], None)
            self.add_dependency(
                dependency_args=dependency, locked_version=locked_version
            )

    def add_dependency(self, dependency_args, locked_version):
        """Adds a dependency to the manager.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        dependency = Dependency(**dependency_args)

        if self.__skip_dependency(dependency, locked_version):
            return
        if locked_version is not None:
            dependency.locked_version = locked_version
            dependency.resolver_info = locked_version.get("resolver_info", None)

        self.locked_versions[dependency.name] = locked_version

        self.seen_dependencies[dependency.name] = dependency
        self.options.add_dependency(dependency)

        with self.registry.provide_temporary() as tmp:
            tmp.provide_value("dependency", dependency)
            resolver = self.registry.require("dependency_resolver")

        path = resolver.resolve()

        if not path:
            return

        # Recurse dependencies (of dependency) before adding self to the
        # dependency cache.
        # Normally this is not a problem, but in certain cases where use flags
        # can't be used (e.g., kernel modules) this is needed.
        if dependency.recurse:
            # We do not require the 'resolve' function to be implemented in
            # dependency projects. Therefore the mandatory=False.
            #
            # str() is needed as waf does not handle unicode in its find_node
            # function (invoked from within recurse).
            self.ctx.recurse([str(path)], mandatory=False)

        self.dependency_cache[dependency.name] = {
            "path": path,
            "recurse": dependency.recurse,
            "added_by": self.ctx.path.abspath(),
        }

    def __skip_dependency(self, dependency, locked_version):
        """Checks if we should skip the dependency.

        :param dependency: A WurfDependency instance.
        :return: True if the dependency should be skipped, otherwise False.
        """
        if dependency.internal:
            if not self.ctx.is_toplevel():
                # Internal dependencies should be skipped, if this is not the
                # top-level wscript
                return True

            if self.skip_internal:
                # Skip internal dependencies if the user has specified
                # the --skip_internal option.
                return True

        if dependency.name in self.seen_dependencies:
            seen_dependency = self.seen_dependencies[dependency.name]

            # We've seen this dependency before. We need to make sure they
            # are specified identically by checking the SHA1
            current = self.ctx.path.abspath()
            added_by = self.dependency_cache[dependency.name]["added_by"]
            if seen_dependency.sha1 != dependency.sha1:
                raise WurfError(
                    f"Adding {dependency.name} in {current}:\n"
                    f"First added by {added_by}:\n"
                    f"SHA1 mismatch:\n{dependency}\n"
                    f"the previous definition was:\n{seen_dependency}"
                )

            # Check if we have a version mismatch
            seen_version = self.locked_versions.get(dependency.name, None)

            if seen_version is None and locked_version is None:
                # Both versions are None, so we are good
                return True

            if seen_version is None:
                # A dependency previously added did not have a locked version
                seen_version = {"sha1": seen_dependency.sha1}
                if seen_dependency.resolver == "git":
                    p = self.dependency_cache[seen_dependency.name]["path"]
                    seen_version["commit_id"] = self.git.current_commit(p)
                    seen_version["resolver_info"] = seen_dependency.resolver_info
            if locked_version is None:
                # The current dependency does not have a locked version
                # this is fine as long as the two dependencies have the same
                # sha1
                return True

            seen_version.pop("resolver_info", None)
            locked_version.pop("resolver_info", None)

            def compare_versions(a, b):
                a = a.copy()
                b = b.copy()
                a.pop("resolver_info", None)
                b.pop("resolver_info", None)
                return a != b

            if compare_versions(seen_version, locked_version):
                raise WurfError(
                    f"Lock entry mismatch!\n"
                    f"Adding {dependency.name} "
                    f"({locked_version or 'unlocked'}) in {current}:\n"
                    f"First added by {added_by} ({seen_version or 'unlocked'})."
                )

            # This dependency is already in the seen_dependencies
            return True

        if not self.__is_toggled_on(dependency):
            # This dependency is not toggled on, so we should skip it
            return True

        return False

    def post_resolve(self):
        """Function called when all dependencies have been resolved."""

        for action in self.post_resolve_actions:
            action(dependency_manager=self)

    def add_post_resolve_action(self, action):
        self.post_resolve_actions.append(action)

    def __is_toggled_on(self, dependency):
        if self.options.lock_paths() or self.options.lock_versions():
            # Always enable toggled dependencies when locking paths or versions
            return True

        if not dependency.optional:
            # Non-optional dependencies are always enabled
            return True

        if dependency.name in self.enabled_dependencies:
            return True

        return False

    def enable_dependency(self, name):
        """Enables a dependency."""
        if name in self.enabled_dependencies:
            raise WurfError(f"Dependency already enabled: {name}")
        self.enabled_dependencies.add(name)
