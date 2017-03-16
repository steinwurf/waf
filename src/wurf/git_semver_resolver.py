#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class GitSemverResolver(object):
    """
    Git Semver Resolver functionality. Checks out a specific semver version.

    Read more about Semantic Versioning here: semver.org
    """

    def __init__(self, git, git_resolver, ctx, semver_selector, working_path,
        dependency):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver_selector: A SemverSelector instance.
        :param working_path: Current working directory as a string. This is the place
            where we should create new folders etc.
        :param dependency: The dependency instance.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver_selector = semver_selector
        self.working_path = working_path
        self.dependency = dependency

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        tags = self.git.tags(cwd=path)
        tag = self.semver_selector.select_tag(
            major=self.dependency.major, tags=tags)

        if not tag:
            self.ctx.fatal(
                'No major tag {} for {} found. Candiates were: {}'.format(
                    self.dependency.major, self.dependency.name, tags))

        # Use the path retuned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_name = tag + '-' + repo_hash
        repo_path = os.path.join(self.working_path, repo_name)

        self.ctx.to_log('wurf: GitSemverResolver name {} -> {}'.format(
            self.dependency.name, repo_path))

        # If the folder for the chosen tag does not exist,
        # then copy the master and checkout the tag
        if not os.path.isdir(repo_path):
            shutil.copytree(src=path, dst=repo_path, symlinks=True)
            self.git.checkout(branch=tag, cwd=repo_path)

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
