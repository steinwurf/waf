#! /usr/bin/env python
# encoding: utf-8

import os
import requests
from urllib.parse import urlparse


class UrlDownload(object):
    def download(self, source, cwd, filename=None):
        assert os.path.exists(cwd)

        # Send an HTTP GET request to the URL
        response = requests.get(source, stream=True)
        response.raise_for_status()

        # If filename is not provided, try to extract it from the URL
        if not filename:
            parsed_url = urlparse(source)

            basename = os.path.basename(parsed_url.path)
            _, extension = os.path.splitext(basename)
            if extension:
                filename = basename

        # If filename is still not available, try to extract it from the
        # Content-Disposition header
        if not filename:
            content_disposition = response.headers.get("content-disposition")
            if content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

        # Check that a filename was found
        assert filename

        path = os.path.join(cwd, filename)
        # Save the file
        with open(path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        return path
