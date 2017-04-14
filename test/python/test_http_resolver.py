import pytest
import mock
import os

from wurf.http_resolver import HttpResolver

def test_http_resolver(test_directory):

    urldownload = mock.Mock()
    dependency = mock.Mock()
    dependency.filename = None

    source = 'http://example.com/file.zip'
    cwd = test_directory.path()

    def create_file(cwd, url, filename):
        assert url == source
        assert filename == None

        #httpdir = test_directory.foo(cwd)
        #httpdir.write_file('file.zip', 'hello_world')

    urldownload.download.side_effect = create_file

    resolver = HttpResolver(urldownload=urldownload, dependency=dependency,
        source=source, cwd=cwd)

    path = resolver.resolve()

    #files = glob.glob(os.path.join(test_directory.path(), 'http-*/file.zip'))

    #assert len(files) == 1
    #assert path == files[0]
