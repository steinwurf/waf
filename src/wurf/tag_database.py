#! /usr/bin/env python
# encoding: utf-8

import json


class TagDatabase(object):
    def __init__(self, ctx):
        """Construct an instance.

        :param ctx: A Waf Context instance.
        """
        self.ctx = ctx
        self.tags = None

    def download_tags(self):
        """
        Download the tag information.
        """
        # Retrieve tags.json from the public URL
        url = (
            "https://raw.githubusercontent.com/steinwurf/tag-registry/master/tags.json"
        )

        # Import tools to be compatible with Python 2 and 3
        try:
            from urllib.request import urlopen, Request
        except ImportError:
            from urllib2 import urlopen, Request

        try:
            # Fetch the json file from the given url
            req = Request(url)
            response = urlopen(req)
            tags_json = response.read()
            self.ctx.to_log(f"Tags downloaded. File size: {len(tags_json)}\n")
            self.tags = json.loads(tags_json)
        except Exception:
            self.tags = {}
            # Log the exception, including the traceback information
            self.ctx.logger.debug(
                f"Could not fetch tags.json from: {url}", exc_info=True
            )

    def project_tags(self, project_name):
        """
        Return the tag information for the given project name.

        :param project_name: The project name to query.
        """
        # Download the tag info - this should be done only once!
        if self.tags is None:
            self.download_tags()
        assert self.tags is not None
        if project_name in self.tags:
            self.ctx.to_log(
                f"Registered tags for {project_name}:\n{self.tags[project_name]}"
            )
            return self.tags[project_name]
        else:
            self.ctx.to_log(f"No registered tags for {project_name}.")
            return None
