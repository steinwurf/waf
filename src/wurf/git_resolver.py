#! /usr/bin/env python
# encoding: utf-8

import os
from .symlink import create_symlink
from .error import RelativeSymlinkError
from .git_checkout_resolver import GitCheckoutResolver


class GitResolver(object):
    """
    Base Git Resolver functionality. Clones/pulls a git repository.
    """

    DEFAULT_BRANCH = "default"

    def __init__(self, git, ctx, dependency, git_url_rewriter, cwd):
        """Construct a new WurfGitResolver instance.

        :param git: A Git instance
        :param ctx: A Waf Context instance.
        :param dependency: The dependency instance.
        :param git_url_rewriter: A GitUrlRewriter instance
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.git = git
        self.ctx = ctx
        self.dependency = dependency
        self.git_url_rewriter = git_url_rewriter
        self.cwd = cwd

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """
        repo_url = self.git_url_rewriter.rewrite_url(self.dependency.source)

        default_repo_path = os.path.join(self.cwd, self.DEFAULT_BRANCH)
        if not os.path.isdir(default_repo_path):
            self.git.clone(
                repository=repo_url,
                directory=default_repo_path,
                cwd=self.cwd,
            )
            self.__create_symlink_to_default_branch(default_repo_path)
        else:
            # We only want to pull if we haven't just cloned. This avoids
            # having to type in the username and password twice when using
            # https as a git protocol.
            try:
                # git pull will fail if the repository is unavailable
                # This is not a problem if we have already downloaded
                # the required version for this dependency
                self.git.pull(cwd=default_repo_path)
            except Exception as e:
                self.ctx.to_log("Exception when executing git pull:")
                self.ctx.to_log(e)

        # If the dependency contains submodules, we also get those
        if self.dependency.pull_submodules:
            self.git.pull_submodules(cwd=default_repo_path)

        return default_repo_path

    def __create_symlink_to_default_branch(self, default_repo_path):
        # Create a symlink to the default branch folder, likely master or main
        default_branch = self.git.default_branch(cwd=default_repo_path)
        link_path = os.path.join(
            self.cwd, GitCheckoutResolver.branch_folder_name(default_branch)
        )
        self.ctx.to_log(
            f"wurf: GitResolver Create symlink {link_path} -> {default_repo_path}"
        )
        try:
            try:
                # We set overwrite True since We need to remove the symlink if it
                # already exists since it may point to an incorrect folder
                create_symlink(
                    from_path=default_repo_path,
                    to_path=link_path,
                    overwrite=True,
                    relative=True,
                )
            except RelativeSymlinkError:
                self.ctx.to_log(
                    "wurf: Using relative symlink failed - fallback to absolute."
                )
                create_symlink(
                    from_path=default_repo_path,
                    to_path=link_path,
                    overwrite=True,
                    relative=False,
                )
        except Exception as ex:
            msg = f"Symlink creation for {self.dependency.name}'s default branch\n"

            # We also want to log the captured output if the command failed
            # with a CalledProcessError, the output would be lost otherwise
            if hasattr(ex, "output"):
                msg += str(ex.output)

            # Using exc_info will attach the current exception information
            # to the log message (including the traceback)
            self.ctx.logger.debug(msg, exc_info=True)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
