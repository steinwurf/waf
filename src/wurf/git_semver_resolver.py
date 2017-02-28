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

    def __init__(self, git, git_resolver, ctx, semver, name, major):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver: The semver module
        :param name: Name of the dependency as a string
        :param major: The major version number to use as an int.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver = semver
        self.name = name
        self.major = major

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        tags = self.git.tags(cwd=path)
        tag = self.select_tag(major=self.major, tags=tags)

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

    def select_tag(self, major, tags):
        """
        Compare the available tags and return the newest tag for the
        specific version.

        :param tags: list of available tags
        :return: the tag to use or None if not tag is compatible
        """
        assert isinstance(major, int), "Major version is not an int"

        # Get tags with matching version
        valid_tags = []

        for tag in tags:
            try:
                t = self.semver.parse(tag)
                if t['major'] != major:
                    continue

                valid_tags.append(tag)
            except ValueError:  # ignore tags we cannot parse
                pass

        if len(valid_tags) == 0:
            return None

        # Now figure out which version is the newest. We may only
        # use versions meeting the version requirement as specified by
        # self.major, self.minor, and self.patch, to ensure compatibility see
        # rules at semver.org

        best_match = valid_tags[0]

        for t in valid_tags:
            if self.semver.match(best_match, "<" + t):
                best_match = t

        return best_match

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
