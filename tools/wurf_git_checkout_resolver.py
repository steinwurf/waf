#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class WurfGitCheckoutResolver(object):
    """
    Git Commit Resolver functionality. Checks out a specific commit.
    """

    def __init__(self, name, cwd, git_resolver, log):
        """
        Creates a new resolver object

        :param url: URL of the Git repository where the dependency
                    can be found
        """
        self.name = name
        self.checkout = checkout
        self.git_resolver = git_resolver
        self.log = log

    def resolve(self, url, checkout):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """
        cwd = os.path.abspath(os.path.expanduser(cwd))

        path = self.git_resolver.resolve(ctx, cwd)

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = self.name + '-' + self.checkout + '-' + repo_hash
        repo_path = os.path.join(cwd, repo_name)

        # If the checkout folder does not exist,
        # then clone from the git repository
        if not os.path.isdir(repo_path):
            shutil.copytree(src=path, dst=repo_path)
            ctx.git_checkout(branch=self.checkout, cwd=repo_path)
        else:
            # If the checkout folder exists, we may need to update it
            ctx.git_pull(cwd=repo_path)

        # If the project contains submodules we also get those
        ctx.git_get_submodules(repository_dir=repo_path)

        return repo_path

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
