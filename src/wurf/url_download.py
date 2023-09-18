#! /usr/bin/env python
# encoding: utf-8

import os
import shutil
from urllib.parse import urlparse
from urllib.request import urlopen, Request

from .error import WurfError


class UrlDownload(object):
    def download(self, source, cwd, filename=None):
        assert os.path.exists(cwd)

        # If filename is not provided, try to extract it from the URL
        if not filename:
            parsed_url = urlparse(source)

            basename = os.path.basename(parsed_url.path)
            _, extension = os.path.splitext(basename)
            if extension:
                filename = basename

        try:
            response = urlopen(Request(source, headers={"User-Agent": "Mozilla"}))
        except Exception as e:
            raise WurfError(f"Failed to download: {source}\n{str(e)}") from e
        # If filename is still not available, try to extract it from the
        # Content-Disposition header
        if not filename:
            filename = response.info().get_filename()

        # Check that a filename was found
        assert filename

        # Send an HTTP GET request to the URL and save the file
        path = os.path.join(cwd, filename)
        with open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        return path
