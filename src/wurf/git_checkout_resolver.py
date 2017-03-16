#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class GitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, git, git_resolver, ctx, dependency, working_path,
        checkout):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param dependency: Dependency instance.
        :param working_path: Current working directory as a string. This is the place
            where we should create new folders etc.
        :param checkout: The branch, tag, or sha1 as a string.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.dependency = dependency
        self.working_path = working_path
        self.checkout = checkout

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        # @todo return path if checkout is the same

        # Use the path retuned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = self.checkout + '-' + repo_hash
        repo_path = os.path.join(self.working_path, repo_name)

        self.ctx.to_log('wurf: GitCheckoutResolver name {} -> {}'.format(
            self.dependency.name, repo_path))

        # If the folder for the chosen version does not exist,
        # then copy the current repo and checkout that version
        if not os.path.isdir(repo_path):
            shutil.copytree(src=path, dst=repo_path, symlinks=True)
            self.git.checkout(branch=self.checkout, cwd=repo_path)
        else:

            if not self.git.is_detached_head(cwd=repo_path):
                # If the checkout is a tag or a commit (we will be in detached
                # HEAD state), then we cannot pull. On the other hand,
                # the pull operation should be executed to update a branch.
                self.git.pull(cwd=repo_path)

        # If the project contains submodules, we also get those
        self.git.pull_submodules(cwd=repo_path)

        # Record the commmit id of the current working copy
        self.dependency.git_commit = self.git.current_commit(cwd=repo_path)

        return repo_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
