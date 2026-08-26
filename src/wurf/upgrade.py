#! /usr/bin/env python
# encoding: utf-8

import contextlib
import json
import os

from .rewrite import open_for_writing
from .tag_selector import select_newest_tag


def locked_version(entry):
    """Describe the version stored in a lock file entry.

    :param entry: The lock file entry as a dict or None
    :return: A short description as a string or None
    """
    if entry is None:
        return None

    if entry.get("resolver_info"):
        return entry["resolver_info"]

    if "commit_id" in entry:
        return entry["commit_id"][:10]

    if "file_hash" in entry:
        return entry["file_hash"][:10]

    return None


def resolved_version(dependency):
    """Describe the version a dependency was resolved to.

    :param dependency: The Dependency instance
    :return: A short description as a string or None
    """
    if dependency.resolver_info:
        return dependency.resolver_info

    if dependency.commit_id:
        return dependency.commit_id[:10]

    return None


class Upgrade(object):
    """Keeps track of the dependencies to upgrade.

    The dependencies named on the command-line are resolved as if no lock
    file existed, and so are the dependencies they pull in. All other
    dependencies stay at the version stored in the lock file.
    """

    def __init__(self, ctx, git, git_url_rewriter, resolve_json_path, names):
        """Construct an instance.

        :param ctx: A Waf Context instance.
        :param git: A Git instance.
        :param git_url_rewriter: A GitUrlRewriter instance.
        :param resolve_json_path: Path to the project's resolve.json file.
        :param names: The dependencies to upgrade as a list of strings. An
            empty list upgrades all dependencies and None means that we are
            not upgrading.
        """
        self.ctx = ctx
        self.git = git
        self.git_url_rewriter = git_url_rewriter
        self.resolve_json_path = resolve_json_path
        self.project_path = os.path.dirname(resolve_json_path)
        self.names = names

        # The number of upgraded dependencies we are currently recursing into
        self.depth = 0

        # The upgraded dependencies stored as
        # name -> (Dependency, lock file entry before the upgrade)
        self.upgraded = {}

        # The dependencies where the checkout in resolve.json was upgraded
        # stored as name -> (old checkout, new checkout)
        self.checkouts = {}

    def active(self):
        """:return: True if dependencies should be upgraded."""
        return self.names is not None

    def named(self, name):
        """:return: True if the dependency was named on the command-line."""
        if not self.active():
            return False

        # Without any names we upgrade everything
        return not self.names or name in self.names

    def upgrading(self, name):
        """:return: True if the dependency should be resolved without lock."""
        if self.named(name):
            return True

        # The dependencies of an upgraded dependency are upgraded as well
        return self.active() and self.depth > 0

    @contextlib.contextmanager
    def recurse(self, upgrading):
        """Track that we are recursing into an upgraded dependency.

        :param upgrading: True if the dependency we recurse into is upgraded
        """
        if upgrading:
            self.depth += 1
        try:
            yield
        finally:
            if upgrading:
                self.depth -= 1

    def add(self, dependency, lock_entry):
        """Store that a dependency was upgraded.

        :param dependency: The Dependency instance
        :param lock_entry: The lock file entry for the dependency before the
            upgrade, None if the dependency was not locked.
        """
        self.upgraded[dependency.name] = (dependency, lock_entry)

    def unknown(self):
        """:return: The named dependencies which were not resolved."""
        if not self.names:
            return []

        return [name for name in self.names if name not in self.upgraded]

    def upgrade_checkout(self, dependency_args):
        """Update the checkout of a dependency to the newest available tag.

        Only git dependencies checked out at a tag are upgraded, a branch or
        a commit id is left untouched.

        :param dependency_args: The dependency as read from resolve.json
        :return: The dependency arguments to use
        """
        if dependency_args.get("resolver") != "git":
            return dependency_args

        if dependency_args.get("method") != "checkout":
            return dependency_args

        source = dependency_args.get("source")

        if not source:
            return dependency_args

        url = self.git_url_rewriter.rewrite_url(source)

        try:
            tags = self.git.remote_tags(url=url, cwd=self.project_path)
        except Exception as e:
            # Without the tags we simply keep the current checkout, the
            # resolve step will report the problem if the repository is
            # unavailable
            self.ctx.to_log(f"Exception when listing the tags of {url}:")
            self.ctx.to_log(e)
            return dependency_args

        checkout = dependency_args["checkout"]

        if checkout not in tags:
            return dependency_args

        newest = select_newest_tag(current=checkout, tags=tags)

        if newest is None:
            return dependency_args

        self.checkouts[dependency_args["name"]] = (checkout, newest)

        return dict(dependency_args, checkout=newest)

    def write(self):
        """Store the upgraded checkouts in the project's resolve.json file."""
        if not self.checkouts:
            return

        with open(self.resolve_json_path, "r") as resolve_file:
            content = resolve_file.read()

        resolve_json = json.loads(content)

        for dependency in resolve_json:
            if dependency["name"] in self.checkouts:
                dependency["checkout"] = self.checkouts[dependency["name"]][1]

        updated = json.dumps(resolve_json, indent=4)

        if content.endswith("\n"):
            updated += "\n"

        with open_for_writing(self.resolve_json_path) as resolve_file:
            resolve_file.write(updated)

    def report(self):
        """Print the versions the upgraded dependencies moved to."""
        changed = False

        # Without a lock file we have nothing to compare the resolved
        # versions with
        locked = any(entry is not None for _, entry in self.upgraded.values())

        for name in sorted(self.upgraded):
            dependency, lock_entry = self.upgraded[name]

            if name in self.checkouts:
                before, after = self.checkouts[name]
                detail = f"{before} -> {after} (resolve.json)"
            else:
                before = locked_version(lock_entry)
                after = resolved_version(dependency)

                if before is None or before == after:
                    continue

                detail = f"{before} -> {after}"

            changed = True
            self.ctx.msg(f'Upgraded "{name}"', detail)

        if not changed and locked:
            self.ctx.msg("Upgrade", "Everything is up to date")
