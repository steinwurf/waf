#! /usr/bin/env python
# encoding: utf-8

# The from . import part was added when moving to
# python3 we suspect that some include paths are not
# the same. Which could be the reason we explicitly
# have to show that the semver module is located in the
# same folder as the dependency_resolve. Note, that this
# happens with the waf packaging where all tools end up
# in the extras folder
from . import semver

import os

class ResolveGitMajorVersion(object):
    """
    Uses the tagged version numbering to follow a specific
    major version number i.e. supports tags like 2.0.1
    """

    def __init__(self, name, git_repository, major_version):
        """
        Creates a new resolver object
        :param name: the name of this dependency resolver
        :param git_repository: URL of the Git repository where the dependency
                               can be found
        :param major_version: The major version number to track (ensures binary
                              compatability)
        """
        self.name = name
        self.git_repository = git_repository
        self.major_version = major_version

    def resolve(self, ctx, path):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        """
        path = os.path.abspath(os.path.expanduser(path))

        # Do we have the master
        master_path = os.path.join(path, self.name + '-master')

        if not os.path.isdir(master_path):
            ctx.git_clone(self.git_repository, master_path, cwd = path)

        ctx.git_pull(cwd = master_path)

        # If the project contains submodules we also get those
        if ctx.git_has_submodules(master_path):
            ctx.git_submodule_sync(cwd = master_path)
            ctx.git_submodule_init(cwd = master_path)
            ctx.git_submodule_update(cwd = master_path)

        tags = ctx.git_tags(cwd = master_path)

        if len(tags) == 0:
            ctx.fatal('No version tags specified for %s '
                      'impossible to track major version' % self.name)

        tag = self.select_tag(tags)

        if not tag:
            ctx.fatal('No compatible tags found %r '
                      'to track major version %d for %s' %
                      (tags, self.major_version, self.name))

        # Do we have the newest tag checked out
        tag_path = os.path.join(path, self.name + '-' + tag)

        if not os.path.isdir(tag_path):
            ctx.git_local_clone(master_path, tag_path, cwd = path)
            ctx.git_checkout(tag, cwd = tag_path)

            # If the project contains submodules we also get those
            if ctx.git_has_submodules(tag_path):
                ctx.git_submodule_sync(cwd = master_path)
                ctx.git_submodule_init(cwd = tag_path)
                ctx.git_submodule_update(cwd = tag_path)


        return tag_path

    def select_tag(self, tags):
        """
        Compare the available tags and return the newest tag for the
        specific major version.
        :param tags: list of availabe tags
        :return: the tag to use or None if not tag is compatible
        """

        # Get tags with matching major version
        valid_tags = []

        for t in tags:

            try:

                if semver.parse(t)['major'] == self.major_version:
                    valid_tags.append(t)

            except ValueError: # ignore tags we cannot parse
                pass

        if len(valid_tags) == 0:
            return None

        # Now figure out which version is the newest. We may only
        # use versions with the same major version as self.major_version
        # to ensure compatibility see rules at semver.org

        best_match = valid_tags[0]

        for t in valid_tags:
            if semver.match(best_match, "<"+t):
                best_match = t

        return best_match

    def __eq__(self, other):
        return ((self.git_repository.lower(), self.major_version) ==
                (other.git_repository.lower(), other.major_version))

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return ((self.git_repository.lower(), self.major_version) <
                (other.git_repository.lower(), other.major_version))

    def __repr__(self):
        f = 'ResolveGitMajorVersion(name=%s, git_repository=%s, major_version=%s)'

        return f % (self.name, self.git_repository, self.major_version)



class ResolveGitFollowMaster(object):
    """
    Follow the master branch
    """

    def __init__(self, name, git_repository):
        """
        Creates a new resolver object
        :param name: the name of this dependency resolver
        :param git_repository: URL of the Git repository where the dependency
                               can be found
        """
        self.name = name
        self.git_repository = git_repository

    def resolve(self, ctx, path):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        """
        path = os.path.abspath(os.path.expanduser(path))

        # Do we have the master
        master_path = os.path.join(path, self.name + '-master')

        if not os.path.isdir(master_path):
            ctx.git_clone(self.git_repository, master_path, cwd = path)

        ctx.git_pull(cwd = master_path)

        # If the project contains submodules we also get those
        if ctx.git_has_submodules(master_path):
            ctx.git_submodule_sync(cwd = master_path)
            ctx.git_submodule_init(cwd = master_path)
            ctx.git_submodule_update(cwd = master_path)

        return master_path

    def __eq__(self, other):
        return self.git_repository.lower() == other.git_repository.lower()

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.git_repository.lower() < other.git_repository.lower()

    def __repr__(self):
        f = 'ResolveGitFollowMaster(name=%s, git_repository=%s)'

        return f % (self.name, self.git_repository)










