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

    def __init__(self, git, git_resolver, ctx, semver_selector, name, major):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver_selector: A SemverSelector instance.
        :param name: Name of the dependency as a string
        :param major: The major version number to use as an int.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver_selector = semver_selector
        self.name = name
        self.major = major

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        tags = self.git.tags(cwd=path)
        tag = self.semver_selector.select_tag(major=self.major, tags=tags)

        if not tag:
            self.ctx.fatal(
                'No major tag {} for {} found. Candiates were: {}'.format(
                    self.major, self.name, tags))

        # Use the parent folder of the path retuned to store different
        # versions of this repository
        repo_folder = os.path.dirname(path)
        tag_path = os.path.join(repo_folder, tag)

        self.ctx.to_log('wurf: GitSemverResolver name {} -> {}'.format(
            self.name, tag_path))

        # If the folder for the chosen tag does not exist,
        # then copy the master and checkout the tag
        if not os.path.isdir(tag_path):
            shutil.copytree(src=path, dst=tag_path, symlinks=True)
            self.git.checkout(branch=tag, cwd=tag_path)

        # If the project contains submodules, we also get those
        self.git.pull_submodules(cwd=tag_path)

        return tag_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
