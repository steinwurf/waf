#! /usr/bin/env python
# encoding: utf-8

import os
import json
from .error import DependencyError


class ExistingCheckoutResolver(object):
    """
    Resolves a specific checkout if a compatible checkout is already checked
    out.
    """

    def __init__(self, ctx, dependency, resolver, checkout, cwd):
        """Construct a new ExistingCheckoutResolver instance.

        :param ctx: A Waf Context instance.
        :param dependency: The Dependency object.
        :param resolver: A resolver instance.
        :param checkout: The branch, tag, or sha1 as a string.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.ctx = ctx
        self.dependency = dependency
        self.resolver = resolver
        self.checkout = checkout
        self.cwd = cwd

    def resolve(self):
        """
        Resolves the path to an existing checkout folder.

        :return: The path to the existing commits, otherwise None.
        """

        commits = self.__load_commits_file()

        # Try to resolve path from commits file
        path = self.__resolve_path(commits=commits)

        if path:
            return path

        # Fallback to the resolver
        path = self.resolver.resolve()

        if not path:
            return None

        assert os.path.isdir(path)

        if "git_commit" in self.dependency:
            # We can only store this if we are asking for a specific commit and
            # not a branch.
            if self.dependency.git_commit.startswith(self.checkout):
                commits[self.dependency.git_commit] = path
        else:
            raise DependencyError(
                msg="No git commit id available", dependency=self.dependency
            )

        self.__store_commits_file(commits=commits)
        return path

    def __load_commits_file(self):

        commit_path = os.path.join(self.cwd, self.dependency.name + ".commits.json")

        if not os.path.isfile(commit_path):
            return {}

        with open(commit_path, "r") as commit_file:
            return json.load(commit_file)

    def __store_commits_file(self, commits):

        commit_path = os.path.join(self.cwd, self.dependency.name + ".commits.json")

        with open(commit_path, "w") as commit_file:
            return json.dump(commits, commit_file, indent=4)

    def __resolve_path(self, commits):

        # Check if the commit is the start of any of the stored commits
        for stored_commit in commits:
            if stored_commit.startswith(self.checkout):
                break
        else:
            self.ctx.to_log(
                "resolve: ExistingCheckoutResolver {} no stored checkout"
                " for commit {}".format(self.dependency.name, self.checkout)
            )
            return None

        path = commits[stored_commit]

        if not os.path.isdir(path):
            self.ctx.to_log(
                "resolve: {} {} contained invalid path {} for commit {}"
                "- removing it".format(
                    self.dependency.name, commits, path, stored_commit
                )
            )

            del commits[stored_commit]
            return None

        else:
            self.ctx.to_log(
                "resolve: ExistingCheckoutResolver name {} -> {}".format(
                    self.dependency.name, path
                )
            )

            return path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
