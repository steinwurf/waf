#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class GitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, git, git_resolver, ctx, name, checkout):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param name: Name of the dependency as a string
        :param checkout: The branch, tag, or sha1 as a string.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.name = name
        self.checkout = checkout

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        # If the requested checkout is the master, just return the path
        if self.checkout == 'master':
            return path

        # Use the parent folder of the path retuned to store different
        # versions of this repository
        repo_folder = os.path.dirname(path)
        checkout_path = os.path.join(repo_folder, self.checkout)

        self.ctx.to_log('wurf: GitCheckoutResolver name {} -> {}'.format(
            self.name, checkout_path))

        # If the folder for the chosen version does not exist,
        # then copy the master and checkout that version
        if not os.path.isdir(checkout_path):
            shutil.copytree(src=path, dst=checkout_path, symlinks=True)
            self.git.checkout(branch=self.checkout, cwd=checkout_path)
        else:

            if not self.git.is_detached_head(cwd=checkout_path):
                # If the checkout is a tag or a commit (we will be in detached
                # HEAD state), then we cannot pull. On the other hand,
                # the pull operation should be executed to update a branch.
                self.git.pull(cwd=checkout_path)

        # If the project contains submodules, we also get those
        self.git.pull_submodules(cwd=checkout_path)

        return checkout_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
