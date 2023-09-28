#! /usr/bin/env python
# encoding: utf-8

import os
import hashlib


class ArchiveResolver(object):
    """
    Extracts an archive
    """

    def __init__(self, ctx, archive_extractor, resolver, cwd):
        """Construct a new instance.

        :param ctx: A Waf Context instance.
        :param archive_extractor: An archive (zip, tar, etc.) extractor
            function.
        :param resolver: The parent resolver responsible for downloading the
            archive.
        :param cwd: Current working directory as a string. This is the place
            where we should create new folders etc.
        """
        self.ctx = ctx
        self.archive_extractor = archive_extractor
        self.resolver = resolver
        self.cwd = cwd

    def resolve(self):
        """
        :return: The path to the resolved dependency as a string.
        """
        path = self.resolver.resolve()

        assert os.path.isfile(path)

        # Use the path returned to create a unique location for extracted files
        extract_hash = hashlib.sha1(path.encode("utf-8")).hexdigest()[:6]

        # The folder for storing the requested checkout
        extract_folder = "extract-" + extract_hash

        extract_path = os.path.join(self.cwd, extract_folder)
        if os.path.exists(extract_path) and len(os.listdir(extract_path)) != 0:
            self.ctx.to_log(
                f"wurf: ArchiveResolver: {extract_path} is not empty. "
                "Skipping extraction."
            )

            return extract_path

        self.archive_extractor(path=path, to_path=extract_path)

        return extract_path
