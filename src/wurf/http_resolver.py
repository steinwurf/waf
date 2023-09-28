#! /usr/bin/env python
# encoding: utf-8

import os
from .error import WurfError


class HttpResolver(object):
    """
    Http Resolver functionality. Downloads a file.
    """

    def __init__(self, ctx, url_download, dependency, cwd):
        """Construct a new instance.

        :param ctx: A Waf Context instance.
        :param url_download: An UrlDownload instance
        :param dependency: The dependency instance.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.ctx = ctx
        self.url_download = url_download
        self.dependency = dependency
        self.cwd = cwd

    def resolve(self):
        """
        Fetches the dependency if necessary.

        :return: The path to the resolved dependency as a string.
        """

        # The folder for storing the file
        folder_path = os.path.join(self.cwd, "download")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        files = os.listdir(folder_path)
        if len(files) > 1:
            raise WurfError(
                f"Expected {folder_path} to at most contain 1 file but found "
                f"{len(files)} files"
            )
        elif len(files) == 1:
            self.ctx.to_log(
                f"wurf: HttpResolver: {folder_path} is not empty. Skipping download."
            )
            filename = files[0]
            if self.dependency.filename and filename != self.dependency.filename:
                raise WurfError(
                    f"Expected {folder_path} to contain {self.dependency.filename} "
                    f"but found {filename}"
                )

            file_path = os.path.join(folder_path, filename)
        else:
            if self.dependency.filename:
                filename = self.dependency.filename
            else:
                filename = None

            file_path = self.url_download.download(
                cwd=folder_path, source=self.dependency.source, filename=filename
            )
        assert os.path.isfile(file_path), "We should have a valid path here!"

        self.dependency.resolver_info = os.path.basename(file_path)

        return file_path
