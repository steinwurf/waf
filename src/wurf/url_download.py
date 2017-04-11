#! /usr/bin/env python
# encoding: utf-8

import cgi
import os

try:
    from urllib.request import urlopen # Python 3
except ImportError:
    from urllib2 import urlopen # Python 2

class UrlDownload(object):

    def url_filename(self, url):
        """ Based on the url return the filename it contains or None if no
        filename is specified.

        URL with a filename:
            http://example.com/file.txt
        URL without a filename:
            http://example.com

        :param url: The URL as a string
        :return: The filename or None if no filename is in the URL.
        """

        filename = os.path.basename(url)

        _, extension = os.path.splitext(filename)

        if not extension:
            return None
        else:
            return filename

    def __response_filename(self, response):
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

        response = urlopen(url=source)

        if not filename:
            filename = self.url_filename(source)

        if not filename:
            filename = self.__response_filename(response)

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
