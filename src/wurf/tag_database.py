#! /usr/bin/env python
# encoding: utf-8


class TagDatabase(object):

    def __init__(self, ctx):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        """
        self.ctx = ctx
        self.tags = None

    def download_tags():
        """
        Download the tag information.
        """
        # Retrieve tags.json from the public URL
        url = "http://files.steinwurf.com/registry/tags.json"

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
            self.ctx.to_log(
                "Tags downloaded. File size: {}\n".format(len(tags_json)))
            tags = json.loads(tags_json)
        except Exception as e:
            tags = {}
            # Log the exception, including the traceback information
            self.ctx.logger.debug(
                "Could not fetch tags.json from: {}".format(url),
                exc_info=True)

    def project_tags(project_name):
        """
        Return the tag information for the given project name.

        :param project_name: The project name to query.
        """
        # Download the tag info - this should be done only once!
        if tags is None:
            self.download_tags()

        if project_name in tags:
            self.ctx.to_log("Registered tags for {}:\n{}".format(
                project_name, tags[project_name]))
            return tags[project_name]
        else:
            self.ctx.to_log("No registered tags for {}.".format(project_name))
            return None
