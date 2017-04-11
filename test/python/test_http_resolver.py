import pytest
import mock
import vcr
import os
import glob
import cgi

try:
    from urllib.request import urlopen # Python 3
except ImportError:
    from urllib2 import urlopen # Python 2

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


@vcr.use_cassette('test/vcr_cassettes/https_resolver.yaml')
def _test_https_resolver_vcr(test_directory):

    dependency = mock.Mock()
    source = 'https://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = test_directory.path()

    resolver = HttpResolver(urlopen=urlopen, dependency=dependency,
        source=source, cwd=cwd)

    path = resolver.resolve()

    files = glob.glob(os.path.join(test_directory.path(), 'http-*/svg'))

    assert len(files) == 1
    assert path == files[0]

@vcr.use_cassette('test/vcr_cassettes/https_resolver.yaml')
def test_https_resolver_vcr(test_directory):

    dependency = mock.Mock()
    source = 'https://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = test_directory.path()

    def url_filename(url):
        filename = os.path.basename(url)

        _, extension = os.path.splitext(filename)

        if not extension:
            return None
        else:
            return filename

    def response_filename(response):
        # Try to get the file name from the headers
        header = response.info().getheader('Content-Disposition', '')

        if not header:
            return None

        _, params = cgi.parse_header(header)
        return params.get('filename', None)

    def download(cwd, source, filename=None):

        response = urlopen(url=source)

        if not filename:
            filename = url_filename(source)

        if not filename:
            filename = response_filename(response)

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

    # path = download(cwd=cwd, source=source)
    path = download(cwd=cwd, source=source, filename='pretty.zip')
    print("PATH {}".format(path))
    assert 0
