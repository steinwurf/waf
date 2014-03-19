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

from waflib.Logs import warn

git_protocols = ['https://', 'git@', 'git://']
git_protocol_handler = ''


def options(opt):
    """
    Add option to specify git protocol
    Options are shown when "python waf -h" is invoked
    :param opt: the Waf OptionsContext
    """
    git_opts = opt.add_option_group('git options')

    git_opts.add_option(
        '--git-protocol', default=None, dest='git_protocol',
        help="Use a specific git protocol to download dependencies. "
             "Supported protocols: {0}".format(git_protocols))

    git_opts.add_option(
        '--check-git-version', default=True, dest='check_git_version',
        help="Specifies if the minimum git version is checked")


def configure(conf):
    """
    The configure function for the dependency resolver tool
    :param conf: the configuration context
    """
    # We need to load git to resolve the dependencies
    conf.load('wurf_git')

    # Check if git meets the minimum requirements
    if conf.options.check_git_version:
        conf.git_check_minimum_version((1, 7, 0))

    # Get the remote url of the parent project
    # to see which protocol prefix (https://, git@, git://)
    # was used when the project was cloned
    parent_url = None
    try:
        parent_url = \
            conf.git_config(['--get', 'remote.origin.url'], cwd=os.getcwd())
    except Exception as e:
        conf.to_log('Exception when executing git config - fallback to '
                    'default protocol! parent_url: {0}'.format(parent_url))
        conf.to_log(e)

    global git_protocol_handler

    if conf.options.git_protocol:
        git_protocol_handler = conf.options.git_protocol

    else:
    # Check if parent protocol is supported
        for g in git_protocols:
            if parent_url and parent_url.startswith(g):
                git_protocol_handler = g
                break
        else:
            git_protocol_handler = 'https://'
            # Unsupported parent protocol, using default
            # Set the protocol handler via the --git-protocol option
            warn("Using default git protocol ({}) for dependencies. "
                 "Use --git-protocol=[proto] to assign another protocol "
                 "for dependencies. "
                 "Supported protocols: {}".format(git_protocol_handler,
                                                  git_protocols))

    if git_protocol_handler not in git_protocols:
        conf.fatal('Unknown git protocol specified: {}, supported protocols '
                   'are {}'.format(git_protocol_handler, git_protocols))


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

    def repository_url(self, ctx):
        """
        Finds the url for the git repository of the dependency.
        :param ctx: A waf ConfigurationContext
        """
        repo_url = self.git_repository
        # The repo url cannot contain a protocol handler,
        # because that is added automatically to match the protocol
        # that was used for checking out the parent project
        if repo_url.count('://') > 0 or repo_url.count('@') > 0:
            ctx.fatal('Repository URL contains the following '
                      'git protocol handler: {}'.format(repo_url))

        if git_protocol_handler not in git_protocols:
            ctx.fatal((
                'Unknown git protocol specified: {}, supported protocols '
                'are {}').format(git_protocol_handler, git_protocols))

        if git_protocol_handler == 'git@':
            if repo_url.startswith('github.com/'):
                # Need to modify the url to support git over SSH
                repo_url = repo_url.replace('github.com/', 'github.com:', 1)
            else:
                ctx.fatal('Unknown SSH host: {}'.format(repo_url))

        return git_protocol_handler + repo_url

    def resolve(self, ctx, path, use_checkout):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """
        path = os.path.abspath(os.path.expanduser(path))

        repo_url = self.repository_url(ctx)

        # Replace all non-alphanumeric characters with _
        #repo_url = re.sub('[^0-9a-zA-Z]+', '_', self.git_repository)

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(repo_url.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_folder = os.path.join(path, self.name + '-' + repo_hash)

        if not os.path.exists(repo_folder):
            ctx.to_log(
                "Creating new repository folder: {}".format(repo_folder))
            os.makedirs(repo_folder)

        # Do we have the master folder?
        master_path = os.path.join(repo_folder, 'master')

        # If the master folder does not exist, do a git clone first
        if not os.path.isdir(master_path):
            ctx.git_clone(repo_url, master_path, cwd=repo_folder)

        # git pull will fail if the github repository is unavailable
        # This is not a problem if we have already downloaded
        # the required major version for this dependency
        try:
            ctx.git_pull(cwd=master_path)
        except Exception as e:
            ctx.to_log('Exception when executing git pull:')
            ctx.to_log(e)

        # If the project contains submodules we also get those
        if ctx.git_has_submodules(master_path):
            ctx.git_submodule_sync(cwd=master_path)
            ctx.git_submodule_init(cwd=master_path)
            ctx.git_submodule_update(cwd=master_path)

        # Do we need a specific checkout? (master, commit or dev branch)

        if use_checkout:
            checkout_path = os.path.join(repo_folder, use_checkout)
            # The master is already up-to-date, but the other checkouts
            # should be cloned to separate directories
            if use_checkout != 'master':
                # If the checkout folder does not exist,
                # then clone from the git repository
                if not os.path.isdir(checkout_path):
                    ctx.git_clone(repo_url, checkout_path, cwd=repo_folder)
                    ctx.git_checkout(use_checkout, cwd=checkout_path)
                else:
                    # If the checkout folder exists, we may need to update it
                    ctx.git_pull(cwd=checkout_path)

                # If the project contains submodules we also get those
                if ctx.git_has_submodules(checkout_path):
                    ctx.git_submodule_sync(cwd=checkout_path)
                    ctx.git_submodule_init(cwd=checkout_path)
                    ctx.git_submodule_update(cwd=checkout_path)

            # The major version of the latest tag should not be larger
            # than the specified major version
            tags = ctx.git_tags(cwd=checkout_path)
            for tag in tags:
                try:
                    if semver.parse(tag)['major'] > self.major_version:
                        ctx.fatal('Tag %r in checkout %r is newer than '
                                  'the required major version %r' %
                                  (tag, use_checkout, self.major_version))
                except ValueError:  # ignore tags we cannot parse
                    pass

            return checkout_path

        tags = []
        # git tags will fail for standalone dependencies
        # This is not a problem if the folder is already present
        # for the required major version of this dependency
        try:
            tags = ctx.git_tags(cwd=master_path)
        except Exception as e:
            ctx.to_log('Exception when executing git tags:')
            ctx.to_log(e)
            # As a fallback, use the existing folder names as tags
            tags = [d for d in os.listdir(repo_folder)
                    if os.path.isdir(os.path.join(repo_folder, d))]

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
            ctx.git_local_clone(master_path, tag_path, cwd=repo_folder)
            ctx.git_checkout(tag, cwd=tag_path)

            # If the project contains submodules we also get those
            if ctx.git_has_submodules(tag_path):
                ctx.git_submodule_sync(cwd=tag_path)
                ctx.git_submodule_init(cwd=tag_path)
                ctx.git_submodule_update(cwd=tag_path)

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
            except ValueError:  # ignore tags we cannot parse
                pass

        if len(valid_tags) == 0:
            return None

        # Now figure out which version is the newest. We may only
        # use versions with the same major version as self.major_version
        # to ensure compatibility see rules at semver.org

        best_match = valid_tags[0]

        for t in valid_tags:
            if semver.match(best_match, "<" + t):
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
        f = ('ResolveGitMajorVersion(name={}, git_repository={}, '
             'major_version={})')

        return f.format(self.name, self.git_repository, self.major_version)
