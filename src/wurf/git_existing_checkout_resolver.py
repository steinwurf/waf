#! /usr/bin/env python
# encoding: utf-8

import os
from .git_resolver import GitResolver
from .git_checkout_resolver import GitCheckoutResolver


class GitExistingCheckoutResolver(object):
    """
    Resolves a specific checkout if a compatible checkout is already checked
    out.
    """

    def __init__(self, ctx, git, dependency, resolver, checkout, cwd):
        """Construct a new GitExistingCheckoutResolver instance.

        :param ctx: A Waf Context instance.
        :param git: A Git instance
        :param dependency: The Dependency object.
        :param resolver: A resolver instance.
        :param checkout: The branch, tag, or sha1 as a string.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.ctx = ctx
        self.git = git
        self.dependency = dependency
        self.resolver = resolver
        self.checkout = checkout
        self.cwd = cwd

    def resolve(self):
        """
        Resolves the path to an existing checkout folder.

        :return: The path to the existing commits, otherwise None.
        """
        # Try to resolve path from commits file
        path = self.__resolve_path()

        if path:
            return path

        return self.resolver.resolve()

    def __resolve_path(self):
        default_branch_cwd = os.path.join(self.cwd, GitResolver.DEFAULT_BRANCH)
        if not os.path.isdir(default_branch_cwd):
            # No default branch, so no cached checkouts
            return None
        checkout_path = os.path.join(
            self.cwd, GitCheckoutResolver.branch_folder_name(self.checkout)
        )
        if os.path.isdir(checkout_path):
            # Checkout is a branch, pull any changes and return path
            self.git.pull(cwd=checkout_path)
            self.dependency.resolver_info = self.checkout
            return checkout_path

        # Checkout is a commit, check if it is cached
        try:
            commit_id = self.git.checkout_to_commit_id(
                cwd=default_branch_cwd, checkout=self.checkout
            )
        except Exception as e:
            # Checkout is not a valid branch or commit, we may need to pull
            self.ctx.to_log(
                f"resolve: GitExistingCheckoutResolver {self.dependency.name} "
                f"failed to resolve {self.checkout} to commit id: {e}"
            )
            return None

        checkout_path = os.path.join(
            self.cwd, GitCheckoutResolver.commit_folder_name(commit_id)
        )

        if os.path.isdir(checkout_path):
            # Commit is cached, return path
            self.dependency.resolver_info = self.checkout
            return checkout_path

        # Checkout not cached
        self.ctx.to_log(
            f"resolve: GitExistingCheckoutResolver {self.dependency.name} "
            f"no stored checkout for {self.checkout}"
        )
        return None

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
