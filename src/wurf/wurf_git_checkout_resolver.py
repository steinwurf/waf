#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class WurfGitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, git, git_resolver, ctx):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx

    def resolve(self, name, cwd, source, checkout, **kwargs):
        """ Fetches the dependency if necessary.

        :param name: Name of the dependency as a string
        :param cwd: Current working directory as a string. This is the place
                    where we should create new folders etc.
        :param source: URL of the repository as a string.
        :param checkout: The branch, tag, or sha1 as a string.
        :param kwargs: Remaining keyword arguments.
        """
        self.ctx.to_log('WurfGitCheckoutResolver resolve')
        cwd = os.path.abspath(os.path.expanduser(cwd))

        path = self.git_resolver.resolve(name=name, cwd=cwd, source=source,
            **kwargs)

        self.ctx.to_log('WurfGitCheckoutResolver path={}'.format(path))

        # Use the path retuned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = name + '-' + checkout + '-' + repo_hash
        repo_path = os.path.join(cwd, repo_name)

        self.ctx.to_log('WurfGitCheckoutResolver repo_name {}'.format(repo_name))
        self.ctx.to_log('WurfGitCheckoutResolver path {} -> repo_path {}'.format(
            path, repo_path))

        # If the checkout folder does not exist,
        # then clone from the git repository
        if not os.path.isdir(repo_path):
            shutil.copytree(src=path, dst=repo_path)
            self.git.checkout(branch=checkout, cwd=repo_path)
        else:

            if not self.git.is_detached_head(cwd=repo_path):
                # If the checkout is a tag or commit (we will be in detached
                # HEAD), then we cannot pull from it. On the other hand if it is
                # a branch we can.
                self.git.pull(cwd=repo_path)

        # If the project contains submodules we also get those
        #
        self.git.pull_submodules(cwd=repo_path)

        return repo_path

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
