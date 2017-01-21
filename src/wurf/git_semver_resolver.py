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

    def __init__(self, git, git_resolver, ctx, semver, name, bundle_path,
        major):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver: The semver module
        :param name: Name of the dependency as a string
        :param bundle_path: Current working directory as a string. This is the place
            where we should create new folders etc.
        :param major: The major version number to use as an int.
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver = semver
        self.name = name
        self.bundle_path = bundle_path
        self.major = major

    def resolve(self):
        """ Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        path = self.git_resolver.resolve()

        assert os.path.isdir(path)

        # Use the path retuned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        tags = self.git.tags(cwd=path)
        tag = self.select_tag(major=self.major, tags=tags)

        if not tag:
            self.ctx.fatal('No major tag {} for {} found. Candiates were: {}'.format(
            self.major, self.name, tags))

        # The folder for storing different versions of this repository
        repo_name = self.name + '-' + tag + '-' + repo_hash
        repo_path = os.path.join(self.bundle_path, repo_name)

        self.ctx.to_log('wurf: GitSemverResolver name {} -> {}'.format(
            self.name, repo_path))

        # If the checkout folder does not exist,
        # then clone from the git repository
        if not os.path.isdir(repo_path):
            shutil.copytree(src=path, dst=repo_path)
            self.git.checkout(branch=tag, cwd=repo_path)

        # If the project contains submodules we also get those
        #
        self.git.pull_submodules(cwd=repo_path)

        return repo_path

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
