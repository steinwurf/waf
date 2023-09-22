#! /usr/bin/env python
# encoding: utf-8

import os
import shutil

from .directory import copy_directory


class GitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    @staticmethod
    def commit_folder_name(commit_id):
        """Return a folder name for a commit.

        :param commit_id: The commit id as a string.
        :return: The folder name as a string.
        """
        return "%s" % commit_id[:10]

    @staticmethod
    def branch_folder_name(branch):
        """Return a folder name for a branch.

        :param branch: The branch name as a string.
        :return: The folder name as a string.
        """
        return "branch-%s" % branch

    def __init__(self, git, resolver, ctx, dependency, checkout, cwd):
        """Construct an instance.

        :param git: A Git instance
        :param ctx: A Waf Context instance.
        :param dependency: Dependency instance.
        :param checkout: The branch, tag, or sha1 as a string.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.git = git
        self.resolver = resolver
        self.ctx = ctx
        self.dependency = dependency
        self.checkout = checkout
        self.cwd = cwd

    def resolve(self):
        """Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """
        path = self.resolver.resolve()

        assert os.path.isdir(path)

        is_branch = self.checkout in self.git.branches(cwd=path)
        if is_branch:
            # If the checkout is a branch, we cannot use the commit id as
            # folder name, as the branch may be updated later.
            folder_name = GitCheckoutResolver.branch_folder_name(self.checkout)
        else:
            commit_id = self.git.checkout_to_commit_id(
                cwd=path,
                checkout=self.checkout,
            )
            folder_name = GitCheckoutResolver.commit_folder_name(commit_id)

        # The folder for storing the requested checkout
        checkout_path = os.path.join(self.cwd, folder_name)

        self.ctx.to_log(
            f"wurf: GitCheckoutResolver name {self.dependency.name} -> {checkout_path}"
        )

        # If the folder for the chosen version does not exist,
        # then copy the master and checkout that version
        if not os.path.isdir(checkout_path):
            try:
                copy_directory(path=path, to_path=checkout_path)
                self.git.checkout(branch=self.checkout, cwd=checkout_path)
            except Exception:
                # The checkout_path must be removed if the checkout is not
                # successful, as the folder would be considered a valid
                # checkout when the user configures again
                def onerror(func, path, exc_info):
                    import stat

                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                    else:
                        raise

                shutil.rmtree(checkout_path, onerror=onerror)
                # The blank "raise" re-raises the last exception
                raise
        elif not self.git.is_detached_head(cwd=checkout_path):
            # If the checkout is a tag or a commit (we will be in detached
            # HEAD state), then we cannot pull. On the other hand,
            # the pull operation should be executed to update a branch.
            self.git.pull(cwd=checkout_path)

        # If the dependency contains submodules, we also get those
        if self.dependency.pull_submodules:
            self.git.pull_submodules(cwd=checkout_path)

        # Record the commmit id of the current working copy
        self.dependency.commit_id = self.git.current_commit(cwd=checkout_path)

        if is_branch:
            self.dependency.resolver_info = self.checkout
            return checkout_path

        current_tag = self.git.current_tag(cwd=checkout_path)
        if current_tag is not None:
            self.dependency.resolver_info = current_tag
        else:
            self.dependency.resolver_info = self.dependency.commit_id[:10]
        return checkout_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
