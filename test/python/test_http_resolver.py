import pytest
import mock
import vcr
import os
import glob


from wurf.http_resolver import HttpResolver

def _test_http_resolver(test_directory):

    retrieve = mock.Mock()
    dependency = mock.Mock()
    source = 'http://example.com/file.zip'
    cwd = test_directory.path()

    def create_file(url, filename):
        assert url == 'http://example.com/file.zip'
        assert filename.endswith('file.zip')
        assert filename.startswith(test_directory.path())

        filename = filename.replace(test_directory.path(), "", 1)
        dirname = os.path.dirname(filename)

        httpdir = test_directory.join(dirname)
        httpdir.write_file('file.zip', 'hello_world')

    retrieve.side_effect = create_file

    resolver = HttpResolver(urlretrieve=retrieve, dependency=dependency,
        source=source, cwd=cwd)

    path = resolver.resolve()

    files = glob.glob(os.path.join(test_directory.path(), 'http-*/file.zip'))

    assert len(files) == 1
    assert path == files[0]


@vcr.use_cassette('test/vcr_cassettes/http_resolver.yaml')
def _test_http_resolver_vcr(test_directory):

    dependency = mock.Mock()
    source = 'http://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = test_directory.path()

    resolver = HttpResolver(urlopen=urlopen, dependency=dependency,
        source=source, cwd=cwd)

    path = resolver.resolve()

    files = glob.glob(os.path.join(test_directory.path(),
        'http-*/louisdx-cxx-prettyprint-*.zip'))

    assert len(files) == 1
    assert path == files[0]


@vcr.use_cassette('test/vcr_cassettes/https_stub_resolver.yaml')
def _test_https_resolver_stub(test_directory):

    dependency = mock.Mock()
    source = 'https://github.com/steinwurf/stub/archive/6.0.0.zip'
    cwd = test_directory.path()

    resolver = HttpResolver(urlopen=urlopen, dependency=dependency,
        source=source, cwd=cwd)

    path = resolver.resolve()

    files = glob.glob(os.path.join(test_directory.path(), 'http-*/6.0.0.zip'))

    assert len(files) == 1
    assert path == files[0]
