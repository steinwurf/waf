#! /usr/bin/env python
# encoding: utf-8

# The from . import part was added when moving to
# python3 we suspect that some include paths are not
# the same. Which could be the reason we explicitly
# have to show that the semver module is located in the
# same folder as the dependency_resolve. Note, that this
# happens with the waf packaging where all tools end up
# in the extras folder
try:
    from . import semver
except:
    import semver


class WurfSemverGitSResolver(object):
    """
    Uses the tagged version numbering to follow a specific version number i.e
    supports tags like 2.0.1
    """

    def __init__(self, name, git_repository, major, minor=None, patch=None):
        """
        Creates a new resolver object
        :param name: the name of this dependency resolver
        :param git_repository: URL of the Git repository where the dependency
                               can be found
        :param major: The major version number to track (ensures binary
                      compatibility), None for newest
        :param minor: The minor version number to track, None for newest
        :param patch: The patch version number to track, None for newest
        """
        self.name = name
        self.git_repository = git_repository
        self.major = major
        self.minor = minor
        self.patch = patch

    def repository_url(self, ctx, protocol_handler):
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

        if protocol_handler not in git_protocols:
            ctx.fatal('Unknown git protocol specified: "{}", supported '
                      'protocols are {}'.format(protocol_handler,
                                                git_protocols))

        if protocol_handler == 'git@':
            # Need to modify the url to support git over SSH
            if repo_url.startswith('github.com/'):
                repo_url = repo_url.replace('github.com/', 'github.com:', 1)
            elif repo_url.startswith('bitbucket.org/'):
                repo_url = repo_url.replace(
                    'bitbucket.org/', 'bitbucket.org:', 1)
            else:
                ctx.fatal('Unknown SSH host: {}'.format(repo_url))

        return protocol_handler + repo_url

    def resolve(self, ctx, path, use_checkout):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """
        path = os.path.abspath(os.path.expanduser(path))

        repo_url = self.repository_url(ctx, git_protocol_handler)

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
        else:
            # We only want to pull if we haven't just cloned. This avoids
            # having to type in the username and password twice when using
            # https as a git protocol.

            try:
                # git pull will fail if the repository is unavailable
                # This is not a problem if we have already downloaded
                # the required version for this dependency
                ctx.git_pull(cwd=master_path)
            except Exception as e:
                ctx.to_log('Exception when executing git pull:')
                ctx.to_log(e)

        # If the project contains submodules we also get those
        ctx.git_get_submodules(master_path)

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
                ctx.git_get_submodules(checkout_path)

            # The major version of the latest tag should not be larger than
            # the specified major version
            tags = ctx.git_tags(cwd=checkout_path)
            for tag in tags:
                try:
                    if semver.parse(tag)['major'] > self.major:
                        ctx.fatal("Tag {} in checkout {} is newer than the "
                                  "required major version {}".format(
                                  tag, use_checkout, self.major))
                except ValueError:  # ignore tags we cannot parse
                    pass

            return checkout_path

        tags = []
        # git tags will fail for standalone dependencies
        # This is not a problem if the folder is already present
        # for the required version of this dependency
        try:
            tags = ctx.git_tags(cwd=master_path)
        except Exception as e:
            ctx.to_log('Exception when executing git tags:')
            ctx.to_log(e)
            # As a fallback, use the existing folder names as tags
            tags = [d for d in os.listdir(repo_folder)
                    if os.path.isdir(os.path.join(repo_folder, d))]
            ctx.to_log('Using the following fallback tags:')
            ctx.to_log(tags)

        if len(tags) == 0:
            ctx.fatal("No version tags specified for {} - impossible to track "
                      "version".format(self.name))

        tag = self.select_tag(tags)

        if not tag:
            ctx.fatal("No compatible tags found {} to track major version {} "
                      "of {}".format(tags, self.major, self.name))

        # Do we have the newest tag checked out
        tag_path = os.path.join(repo_folder, tag)

        if not os.path.isdir(tag_path):
            ctx.git_local_clone(master_path, tag_path, cwd=repo_folder)
            ctx.git_checkout(tag, cwd=tag_path)

            # If the project contains submodules we also get those
            ctx.git_get_submodules(tag_path)

        return tag_path

    def select_tag(self, tags):
        """
        Compare the available tags and return the newest tag for the
        specific version.
        :param tags: list of available tags
        :return: the tag to use or None if not tag is compatible
        """

        # Get tags with matching version
        valid_tags = []

        for tag in tags:
            try:
                t = semver.parse(tag)
                if (self.major is not None and t['major'] != self.major) or \
                   (self.minor is not None and t['minor'] != self.minor) or \
                   (self.patch is not None and t['patch'] != self.patch):
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
            if semver.match(best_match, "<" + t):
                best_match = t

        return best_match

    def __eq__(self, other):
        s = (self.git_repository.lower(),
             self.major,
             self.minor,
             self.patch)
        o = (other.git_repository.lower(),
             other.major,
             other.minor,
             other.patch)
        return s == o

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        s = (self.git_repository.lower(),
             self.major,
             self.minor,
             self.patch)
        o = (other.git_repository.lower(),
             other.major,
             other.minor,
             other.patch)
        return s < o

    def __repr__(self):
        f = ('ResolveVersion(name={}, git_repository={}, major={}, minor={}, '
             'patch={})')

        return f.format(
            self.name, self.git_repository, self.major, self.minor, self.patch)


class ResolveGitCommit(object):
    """
    @todo
    """

    def __init__(self, name, git_repository, commit):
        """
        Creates a new resolver object
        :param name: the name of this dependency resolver
        :param git_repository: URL of the Git repository where the dependency
                               can be found
        :param major: The major version number to track (ensures binary
                      compatibility), None for newest
        :param minor: The minor version number to track, None for newest
        :param patch: The patch version number to track, None for newest
        """
        self.name = name
        self.git_repository = git_repository
        self.commit = commit

    def repository_url(self, ctx, protocol_handler):
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

        if protocol_handler not in git_protocols:
            ctx.fatal('Unknown git protocol specified: "{}", supported '
                      'protocols are {}'.format(protocol_handler,
                                                git_protocols))

        if protocol_handler == 'git@':
            # Need to modify the url to support git over SSH
            if repo_url.startswith('github.com/'):
                repo_url = repo_url.replace('github.com/', 'github.com:', 1)
            elif repo_url.startswith('bitbucket.org/'):
                repo_url = repo_url.replace(
                    'bitbucket.org/', 'bitbucket.org:', 1)
            else:
                ctx.fatal('Unknown SSH host: {}'.format(repo_url))

        return protocol_handler + repo_url

    def resolve(self, ctx, path, use_checkout):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """
        path = os.path.abspath(os.path.expanduser(path))

        repo_url = self.repository_url(ctx, git_protocol_handler)

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
        else:
            # We only want to pull if we haven't just cloned. This avoids
            # having to type in the username and password twice when using
            # https as a git protocol.

            try:
                # git pull will fail if the repository is unavailable
                # This is not a problem if we have already downloaded
                # the required version for this dependency
                ctx.git_pull(cwd=master_path)
            except Exception as e:
                ctx.to_log('Exception when executing git pull:')
                ctx.to_log(e)

        # If the project contains submodules we also get those
        ctx.git_get_submodules(master_path)

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
                ctx.git_get_submodules(checkout_path)

            return checkout_path

        # Do we have the newest tag checked out
        commit_path = os.path.join(repo_folder, self.commit)

        if not os.path.isdir(commit_path):
            ctx.git_local_clone(master_path, commit_path, cwd=repo_folder)
            ctx.git_checkout(self.commit, cwd=commit_path)

            # If the project contains submodules we also get those
            ctx.git_get_submodules(commit_path)

        return commit_path

    # def __eq__(self, other):
    #     s = (self.git_repository.lower(),
    #          self.major,
    #          self.minor,
    #          self.patch)
    #     o = (other.git_repository.lower(),
    #          other.major,
    #          other.minor,
    #          other.patch)
    #     return s == o

    # def __ne__(self, other):
    #     return not self == other

    # def __lt__(self, other):
    #     s = (self.git_repository.lower(),
    #          self.major,
    #          self.minor,
    #          self.patch)
    #     o = (other.git_repository.lower(),
    #          other.major,
    #          other.minor,
    #          other.patch)
    #     return s < o

    def __repr__(self):
        f = ('ResolveGitCommit(name={}, git_repository={}, commit={})')

        return f.format(
            self.name, self.git_repository, self.commit)
