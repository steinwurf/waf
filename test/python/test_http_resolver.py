import pytest
import mock
import os

from wurf.http_resolver import HttpResolver


def test_http_resolver(test_directory):

    url_download = mock.Mock()
    dependency = mock.Mock()
    dependency.filename = None

    http_source = 'http://example.com/file.zip'
    cwd = test_directory.path()

    def create_file(cwd, source, filename):
        assert http_source == source
        assert filename == None

        httpdir = test_directory.from_path(cwd)
        httpdir.write_binary('file.zip', b'hello_world')

        return os.path.join(httpdir.path(), 'file.zip')

    url_download.download.side_effect = create_file

    resolver = HttpResolver(url_download=url_download, dependency=dependency,
        source=http_source, cwd=cwd)

    path = resolver.resolve()

    assert test_directory.contains_file('http-*/file.zip')


def test_http_resolver_filename(test_directory):

    url_download = mock.Mock()
    dependency = mock.Mock()
    dependency.filename = 'foo.zip'

    http_source = 'http://example.com/file.zip'
    cwd = test_directory.path()

    def create_file(cwd, source, filename):
        assert http_source == source
        assert filename == 'foo.zip'

        httpdir = test_directory.from_path(cwd)
        httpdir.write_binary('foo.zip', b'hello_world')

        return os.path.join(httpdir.path(), 'foo.zip')

    url_download.download.side_effect = create_file

    resolver = HttpResolver(url_download=url_download, dependency=dependency,
        source=http_source, cwd=cwd)

    path = resolver.resolve()

    assert test_directory.contains_file('http-*/foo.zip')
