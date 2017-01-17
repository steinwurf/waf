#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os

class GitResolver(object):
    """
    Base Git Resolver functionality. Clones/pulls a git repository.
    """

    def __init__(self, git, url_resolver, ctx, name, bundle_path, source):
        """ Construct a new WurfGitResolver instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitUrlResolver instance.
        :param ctx: A Waf Context instance.
        :param name: The name of the dependency as a string
        :param bundle_path: Current working directory as a string. This is the place
            where we should create new folders etc.
        :param source: THe URL of the dependency as a string
        """
        self.git = git
        self.url_resolver = url_resolver
        self.ctx = ctx
        self.name = name
        self.bundle_path = bundle_path
        self.source = source

        assert os.path.isabs(self.bundle_path)

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """
        repo_url = self.url_resolver.rewrite_url(url=self.source)

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(repo_url.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = self.name + '-master-' + repo_hash
        repo_path = os.path.join(self.bundle_path, repo_name)

        self.ctx.to_log('wurf: GitResolver name {} -> {}'.format(
            self.name, repo_path))

        # If the master folder does not exist, do a git clone first
        if not os.path.isdir(repo_path):
            self.git.clone(repository=repo_url, directory=repo_name,
                cwd=self.bundle_path)
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
