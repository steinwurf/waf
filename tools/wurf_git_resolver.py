#! /usr/bin/env python
# encoding: utf-8


class WurfGitSResolver(object):
    """
    Base Git Resolver functionality. Clones/pulls a git repository.
    """

    def __init__(self, url):
        """
        Creates a new resolver object

        :param url: URL of the Git repository where the dependency
                    can be found
        """
        self.url = url

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

    def resolve(self, ctx, cwd):
        """
        Fetches the dependency if necessary.
        :param ctx: A waf ConfigurationContext
        :param path: The path where the dependency should be located
        :param use_checkout: If not None the given checkout will be used
        """
        path = os.path.abspath(os.path.expanduser(cwd))

        repo_url = self.repository_url(ctx, git_protocol_handler)

        # Use the first 6 characters of the SHA1 hash of the repository url
        # to uniquely identify the repository
        repo_hash = hashlib.sha1(repo_url.encode('utf-8')).hexdigest()[:6]

        # The folder for storing different versions of this repository
        repo_folder = os.path.join(path, self.name + '-' + repo_hash)

        if not os.path.exists(repo_folder):
            ctx.to_log("Creating new repository folder: {}".format(repo_folder))
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

        return master_path


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
