#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

from .directory import copy_directory


class GitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, git, resolver, ctx, dependency, checkout, cwd):
        """Construct an instance.

        :param git: A Git instance
        :param resolver: A GitResolver instance.
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

        if self.git.current_branch(cwd=path) == self.checkout:
            return path

        if self.git.current_commit(cwd=path) == self.checkout:
            return path

        # Use the path returned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode("utf-8")).hexdigest()[:6]

        # The folder for storing the requested checkout
        folder_name = self.checkout + "-" + repo_hash
        checkout_path = os.path.join(self.cwd, folder_name)

        self.ctx.to_log(
            "wurf: GitCheckoutResolver name {} -> {}".format(
                self.dependency.name, checkout_path
            )
        )

        # If the folder for the chosen version does not exist,
        # then copy the master and checkout that version
        if not os.path.isdir(checkout_path):
            try:
                copy_directory(path=path, to_path=checkout_path)

                print(f"OK HERE {self.checkout = }")

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
        else:

            if not self.git.is_detached_head(cwd=checkout_path):
                # If the checkout is a tag or a commit (we will be in detached
                # HEAD state), then we cannot pull. On the other hand,
                # the pull operation should be executed to update a branch.
                self.git.pull(cwd=checkout_path)

        # If the project contains submodules, we also get those
        if self.dependency.pull_submodules:
            self.git.pull_submodules(cwd=checkout_path)

        # Record the commmit id of the current working copy
        self.dependency.git_commit = self.git.current_commit(cwd=checkout_path)

        return checkout_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
