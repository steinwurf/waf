#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib

class GitResolver(object):
    """
    Base Git Resolver functionality. Clones/pulls a git repository.
    """

    def __init__(self, git, ctx, name, cwd, source):
        """ Construct a new WurfGitResolver instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitUrlResolver instance.
        :param ctx: A Waf Context instance.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        :param name: The name of the dependency as a string
        :param source: The URL of the dependency as a string
        """
        self.git = git
        self.ctx = ctx
        self.name = name
        self.cwd = cwd
        self.source = source

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """
        repo_url = self.source

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(repo_url.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = 'master-' + repo_hash
        repo_path = os.path.join(self.cwd, repo_name)

        # If the master folder does not exist, do a git clone first
        if not os.path.isdir(repo_path):
            self.git.clone(repository=repo_url, directory=repo_name,
                cwd=self.cwd)
        else:
            # We only want to pull if we haven't just cloned. This avoids
            # having to type in the username and password twice when using
            # https as a git protocol.
            try:
                # git pull will fail if the repository is unavailable
                # This is not a problem if we have already downloaded
                # the required version for this dependency
                self.git.pull(cwd=repo_path)
            except Exception as e:
                self.ctx.to_log('Exception when executing git pull:')
                self.ctx.to_log(e)

        assert os.path.isdir(repo_path), "We should have a valid path here!"

        # If the project contains submodules we also get those
        self.git.pull_submodules(cwd=repo_path)

        return repo_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
