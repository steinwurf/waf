#! /usr/bin/env python
# encoding: utf-8

import os
import shutil

from .error import DependencyError

class GitSemverResolver(object):
    """
    Git Semver Resolver functionality. Checks out a specific semver version.

    Read more about Semantic Versioning here: semver.org
    """

    def __init__(self, git, git_resolver, ctx, semver_selector, dependency):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver_selector: A SemverSelector instance.
        :param dependency: The dependency instance.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver_selector = semver_selector
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
            raise DependencyError(
                msg="No tag found for major version {}, candiates "
                    "were {}".format(self.dependency.major, tags),
                dependency=self.dependency)

        # Use the parent folder of the path retuned to store different
        # versions of this repository
        repo_folder = os.path.dirname(path)
        tag_path = os.path.join(repo_folder, tag)

        self.ctx.to_log('wurf: GitSemverResolver name {} -> {}'.format(
            self.dependency.name, tag_path))

        # If the folder for the chosen tag does not exist,
        # then copy the master and checkout the tag
        if not os.path.isdir(tag_path):
            shutil.copytree(src=path, dst=tag_path, symlinks=True)
            self.git.checkout(branch=tag, cwd=tag_path)

        # If the project contains submodules, we also get those
        self.git.pull_submodules(cwd=tag_path)

        # Record the commmit id of the current working copy
        self.dependency.git_commit = self.git.current_commit(cwd=tag_path)
        self.dependency.git_tag = tag

        return tag_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
