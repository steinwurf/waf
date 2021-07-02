#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib

from .directory import copy_directory
from .directory import remove_directory
from .error import WurfError


class PostResolveRun(object):
    """
    Runs a command in the directory of a resolved dependency.
    """

    def __init__(self, resolver, ctx, run, cwd):

        """Construct a new instance.

        :param resolver: A resolver instance.
        :param ctx: A Waf Context instance.
        :param run: The command to run and a string or list.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.resolver = resolver
        self.ctx = ctx
        self.run = run
        self.cwd = cwd

    def resolve(self):
        """
        Runs a command in the directory of a

        :return: The path to the resolved dependency as a string.
        """
        path = self.resolver.resolve()

        if os.path.isfile(path):
            path = os.path.dirname(path)

        # Use the first 6 characters of the SHA1 hash of the run command
        # and the path
        hash_data = str(self.run) + path
        run_hash = hashlib.sha1(hash_data.encode("utf-8")).hexdigest()[:6]

        # The folder for storing the master branch of this repository
        folder_name = "run-" + run_hash
        run_path = os.path.join(self.cwd, folder_name)

        # If the folder already exists we are done
        if os.path.isdir(run_path):
            return run_path

        try:
            copy_directory(path=path, to_path=run_path)
            self.ctx.cmd_and_log(cmd=self.run, cwd=run_path)

        except WurfError:

            # If we do not succeed clean up and make sure we start from
            # scratch next time around
            if os.path.isdir(run_path):
                remove_directory(path=run_path)
            raise

        return run_path
