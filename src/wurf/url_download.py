#! /usr/bin/env python
# encoding: utf-8

import cgi
import os

try:
    # Python 3
    from urllib.request import urlopen
    from urllib.parse import urlparse

except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urlparse import urlparse

class UrlDownload(object):

    def _url_filename(self, url):
        """ Based on the url return the filename it contains or None if no
        filename is specified.

        URL with a filename:
            http://example.com/file.txt
        URL without a filename:
            http://example.com

        :param url: The URL as a string
        :return: The filename or None if no filename is in the URL.
        """

        parsed = urlparse(url)

        if not parsed.path:
            return None

        filename = os.path.basename(parsed.path)

        _, extension = os.path.splitext(filename)

        if not extension:
            return None
        else:
            return filename

    def _response_filename(self, response):
        """ Returns the filename contained in the HTTP Content-Disposition
        header.
        """
        # Try to get the file name from the headers
        header = response.info().getheader('Content-Disposition', '')

        if not header:
            return None

        _, params = cgi.parse_header(header)
        return params.get('filename', None)

    def download(self, cwd, source, filename=None):
        """ Download the file specified by the source.

        :param cwd: The directory where to download the file.
        :param source: The URL of the file to download.
        :param filename: The filename to store the file under.
        """

        response = urlopen(url=source)

        if not filename:
            filename = self._url_filename(source)

        if not filename:
            filename = self._response_filename(response)

        assert filename
        assert os.path.isdir(cwd)

        filepath = os.path.join(cwd, filename)

        # From http://stackoverflow.com/a/1517728
        CHUNK = 16 * 1024
        with open(filepath, 'wb') as f:
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)

        return filepath
