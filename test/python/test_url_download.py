import pytest
import mock
import vcr

from wurf.url_download import UrlDownload

def test_url_download_url_filename():
    download = UrlDownload()

    assert download.url_filename('http://example.com') == None
    assert download.url_filename('http://example.com/data.txt') == 'data.txt'


@vcr.use_cassette('test/vcr_cassettes/https_resolver.yaml')
def _test_url_download_vcr(test_directory):

    dependency = mock.Mock()
    source = 'https://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = test_directory.path()

    download = UrlDownload()

    path = download.download(cwd=cwd, source=source, filename='test.zip')

    assert os.path.join(cwd, 'test.zip') == path
