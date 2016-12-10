#! /usr/bin/env python
# encoding: utf-8

import hashlib
import os
import shutil

class WurfGitSemverResolver(object):
    """
    Git Semver Resolver functionality. Checks out a specific semver version.

    Read more about Semantic Versioning here: semver.org
    """

    def __init__(self, git, git_resolver, ctx, semver):
        """ Construct an instance.

        :param git: A WurfGit instance
        :param url_resolver: A WurfGitResolver instance.
        :param ctx: A Waf Context instance.
        :param semver: The semver module
        """
        self.git = git
        self.git_resolver = git_resolver
        self.ctx = ctx
        self.semver = semver

    def resolve(self, name, cwd, source, major, **kwargs):
        """ Fetches the dependency if necessary.

        :param name: Name of the dependency as a string
        :param cwd: Current working directory as a string. This is the place
                    where we should create new folders etc.
        :param source: URL of the repository as a string.
        :param major: The major version number to use as an int.
        :param kwargs: Remaining keyword arguments.
        """
        cwd = os.path.abspath(os.path.expanduser(cwd))

        path = self.git_resolver.resolve(name=name, cwd=cwd, source=source,
            **kwargs)

        # Use the path retuned to create a unique location for this checkout
        repo_hash = hashlib.sha1(path.encode('utf-8')).hexdigest()[:6]

        tags = self.git.tags(cwd=path)
        tag = self.select_tag(major=major, tags=tags)

        if not tag:
            self.ctx.fatal('No major tag {} for {} found. Candiates were: {}'.format(
            major, name, tags))

        # The folder for storing different versions of this repository
        repo_name = name + '-' + tag + '-' + repo_hash
        repo_path = os.path.join(cwd, repo_name)

        self.ctx.to_log('git semver repo_name {}'.format(repo_name))
        self.ctx.to_log('git semver path {} -> repo_path {}'.format(
            path, repo_path))

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
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
