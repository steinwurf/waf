#! /usr/bin/env python
# encoding: utf-8

import os
import tempfile
import shutil


class GitResolver(object):
    """
    Base Git Resolver functionality. Clones/pulls a git repository.
    """

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

        expected_default_branches = ["master", "main"]
        for default_branch in expected_default_branches:
            folder_name = f"branch-{default_branch}"
            default_repo_path = os.path.join(self.cwd, folder_name)
            if os.path.isdir(default_repo_path):
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
                break
        else:
            # clone the repo to a temporary folder and move it to a
            # folder named after the default branch
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_repo_dir = os.path.join(tmpdir, "repo")
                self.git.clone(
                    repository=repo_url,
                    directory=tmp_repo_dir,
                    cwd=self.cwd,
                )

                default_repo_path = os.path.join(
                    self.cwd,
                    f"branch-{self.git.default_branch(cwd=tmp_repo_dir)}",
                )
                shutil.move(tmp_repo_dir, default_repo_path)

        assert os.path.isdir(default_repo_path), "Path not valid!"

        # If the project contains submodules we also get those
        if self.dependency.pull_submodules:
            self.git.pull_submodules(cwd=default_repo_path)

        self.dependency.git_commit = self.git.current_commit(
            cwd=default_repo_path,
        )

        return default_repo_path

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
