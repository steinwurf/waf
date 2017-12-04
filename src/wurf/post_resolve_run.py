#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


class PostResolveRun(object):
    """
    Runs a command in the directory of a resolved dependency.
    """

    def __init__(self, ctx, run, cwd):

        """ Construct a new WurfGitResolver instance.

        :param git: A Git instance
        :param ctx: A Waf Context instance.
        :param dependency: The dependency instance.
        :param git_url_rewriter: A GitUrlRewriter instance
        :param source: The URL of the dependency as a string
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.resolve = resolver
        self.ctx = ctx
        self.dependency = dependency
        self.git_url_rewriter = git_url_rewriter
        self.run = run
        self.cwd = cwd

    def resolve(self):
        """
        Runs a command in the directory of a

        :return: The path to the resolved dependency as a string.
        """
        path = self.resolver.resolve()

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        run_hash = hashlib.sha1(self.run.encode('utf-8')).hexdigest()[:6]

        # The folder for storing the master branch of this repository
        folder_name = 'run-' + run_hash
        run_path = os.path.join(self.cwd, folder_name)

        # If the folder already exists we are done
        if os.path.isdir(run_path):
            return run_path

        shutil.copytree(src=path, dst=tag_path, symlinks=True)

        self.ctx.command_and_log(XXXXXXXXXX)

        return run_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
