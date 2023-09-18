#! /usr/bin/env python
# encoding: utf-8

import os
import re


class Git(object):
    def __init__(self, git_binary, ctx):
        """Construct a new Git instance.

        :param git_binary: A string containing the path to a git executable.
        :param ctx: A Waf Context instance.
        """
        self.git_binary = git_binary
        self.ctx = ctx

    def version(self):
        """
        Runs 'git version' and return the version information as a tuple

        Example:

            If the output looks like "git version 1.8.1.msysgit.1"
            we just extract the integers i.e. (1.8.1.1)
        """
        args = [self.git_binary, "version"]
        output = self.ctx.cmd_and_log(args).strip()

        int_list = [int(s) for s in re.findall("\\d+", output)]
        return tuple(int_list)

    def is_git_repository(self, cwd):
        """
        Tries to determine if the cwd is a git repository
        """

        # Approach outlined here:
        # https://stackoverflow.com/a/2180367/1717320

        git_dir = os.path.join("cwd", ".git")
        if os.path.isdir(git_dir):
            return True

        try:
            args = [self.git_binary, "rev-parse", "--git-dir"]
            self.ctx.cmd_and_log(args, cwd=cwd)
            return True
        except Exception:
            return False

    def current_commit(self, cwd):
        """
        Runs 'git rev-parse HEAD' parse and return the commit id (SHA1) of the
        commit currently checked out into the working copy.
        """
        args = [self.git_binary, "rev-parse", "HEAD"]
        output = self.ctx.cmd_and_log(args, cwd=cwd).strip()

        return output

    def current_tag(self, cwd):
        """
        Check if the current commmit matches a tag

        :return: The current tags as a string otherwise None
        """
        args = [self.git_binary, "tag", "--points-at", self.current_commit(cwd)]

        output = self.ctx.cmd_and_log(args, cwd=cwd).strip()

        if not output:
            return None
        else:
            # Return the first tag as a commit may have multiple tags
            return output.splitlines()[0]

    def clone(self, repository, directory, cwd, branch=None, depth=None):
        """
        Runs 'git clone <repository> <directory>' in the directory cwd.
        """
        args = [self.git_binary, "clone", repository, directory]

        if depth:
            args += ["--depth", str(depth)]

        if branch:
            args += ["--branch", branch]

        self.ctx.cmd_and_log(args, cwd=cwd)

    def pull(self, cwd):
        """
        Runs 'git pull' in the directory cwd
        """

        args = [self.git_binary, "pull"]
        self.ctx.cmd_and_log(args, cwd=cwd)

    def branch(self, cwd):
        """
        Runs 'git branch' and returns the current branch and a list of
        additional branches
        """
        args = [self.git_binary, "branch"]
        o = self.ctx.cmd_and_log(args, cwd=cwd)

        branch = o.split("\n")
        branch = [b for b in branch if b != ""]

        current = ""
        others = []

        for b in branch:
            if b.startswith("*"):
                current = b[1:].strip()
            else:
                others.append(b)

        if current == "":
            self.ctx.fatal("Failed to locate current branch")

        return current, others

    def current_branch(self, cwd):
        """
        Uses git.branch(...) but only returns the current one
        """
        current, _ = self.branch(cwd=cwd)
        return current

    def is_detached_head(self, cwd):
        """
        Checks if the repository is in detached HEAD state. See learn what this
        means read here:

            https://git-scm.com/docs/git-checkout
        """
        current, _ = self.branch(cwd=cwd)

        # Different git versions denote the detached HEAD state differently,
        # possible variants are the following:
        # * (no branch)
        # * (detached from waf-1.9.7)
        # * (HEAD detached at waf-1.9.7)
        return current.startswith("(") and current.endswith(")")

    def checkout(self, branch, cwd):
        """
        Runs 'git checkout branch'
        """
        args = [self.git_binary, "checkout", "--force", branch]
        self.ctx.cmd_and_log(args, cwd=cwd)

    def has_submodules(ctx, cwd):
        """
        Returns true if the repository in directory cwd contains the
        .gitmodules file.
        """
        return os.path.isfile(os.path.join(cwd, ".gitmodules"))

    def sync_submodules(self, cwd):
        """
        Runs 'git submodule sync' in the directory cwd
        """
        args = [self.git_binary, "submodule", "sync", "--recursive"]
        self.ctx.cmd_and_log(args, cwd=cwd)

    def update_submodules(self, cwd):
        """
        Runs 'git submodule update' in the directory cwd
        """
        args = [self.git_binary, "submodule", "update", "--recursive", "--init"]

        self.ctx.cmd_and_log(args, cwd=cwd)

    def pull_submodules(self, cwd):
        """
        Runs 'git submodule sync', 'git submodule init', and
        'git submodule update' unless the repository doesn't have submodules.
        """
        if self.has_submodules(cwd=cwd):
            self.sync_submodules(cwd=cwd)
            self.update_submodules(cwd=cwd)

    def tags(self, cwd):
        """
        Runs 'git tag -l' in the directory cwd and returns the tags

        :param cwd: The current working directory as a string
        """
        args = [self.git_binary, "tag", "-l"]
        output = self.ctx.cmd_and_log(args, cwd=cwd)

        tags = output.split("\n")
        return [t for t in tags if t != ""]

    def remote_origin_url(self, cwd):
        """
        Runs 'git config --get remote.origin.url' in the directory cwd and
        returns the value

        :param cwd: The current working directory as a string
        """
        args = [self.git_binary, "config", "--get", "remote.origin.url"]
        output = self.ctx.cmd_and_log(args, cwd=cwd)

        return output.strip()
