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
#import re
import hashlib
import shutil

from waflib.Logs import debug

##def onerror(func, path, exc_info):
##    # path contains the path of the file that couldn't be removed
##    # let's just assume that it's read-only and unlink it.
##    # Usage: shutil.rmtree(full_folder_path, onerror = onerror)
##    import stat
##    os.chmod( path, stat.S_IWRITE )
##    os.unlink( path )

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

    def resolve(self, ctx, path, use_master):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_master: If true the master will be used
        """
        path = os.path.abspath(os.path.expanduser(path))

        # Replace all non-alphanumeric characters with _
        #repo_url = re.sub('[^0-9a-zA-Z]+', '_', self.git_repository)

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(self.git_repository.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_folder = os.path.join(path, self.name + '-' + repo_hash)

        if not os.path.exists(repo_folder):
            ctx.to_log("Creating new repository folder: {}".format(repo_folder))
            os.makedirs(repo_folder)

        # Do we have the master folder?
        master_path = os.path.join(repo_folder, 'master')

##        # If yes, we need to verify the remote url in the master folder
##        if os.path.isdir(master_path):
##            remote_url = ctx.git_config_get_remote_url(cwd = master_path)
##            # If it does not match the repository url
##            if remote_url != self.git_repository:
##                ctx.to_log("Remote_url mismatch, expected url: {}".format(self.git_repository))
##                # Delete all folders for this dependency
##                folders = [ master_path ]
##                tags = ctx.git_tags(cwd = master_path)
##                for tag in tags:
##                    tag_path = os.path.join(path, self.name + '-' + tag)
##                    if os.path.isdir(tag_path):
##                        folders.append(tag_path)
##                for folder in folders:
##                    ctx.to_log("Deleting folder: {}".format(folder))
##                    shutil.rmtree(folder, onerror = onerror)


        # If the master folder does not exist, do a git clone first
        if not os.path.isdir(master_path):
            ctx.git_clone(self.git_repository, master_path, cwd = repo_folder)

        ctx.git_pull(cwd = master_path)

        # If the project contains submodules we also get those
        if ctx.git_has_submodules(master_path):
            ctx.git_submodule_sync(cwd = master_path)
            ctx.git_submodule_init(cwd = master_path)
            ctx.git_submodule_update(cwd = master_path)

        if use_master:
            return master_path

        tags = ctx.git_tags(cwd = master_path)

        if len(tags) == 0:
            ctx.fatal('No version tags specified for %r '
                      '- impossible to track major version' % self.name)

        tag = self.select_tag(tags)

        if not tag:
            ctx.fatal('No compatible tags found %r '
                      'to track major version %d of %s' %
                      (tags, self.major_version, self.name))

        # Do we have the newest tag checked out
        tag_path = os.path.join(repo_folder, tag)

        if not os.path.isdir(tag_path):
            ctx.git_local_clone(master_path, tag_path, cwd = repo_folder)
            ctx.git_checkout(tag, cwd = tag_path)

            # If the project contains submodules we also get those
            if ctx.git_has_submodules(tag_path):
                ctx.git_submodule_sync(cwd = tag_path)
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

    def resolve(self, ctx, path, use_master):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_master: Is ignored for this resolver
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










