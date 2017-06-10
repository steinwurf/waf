import vcr
import os

from wurf.url_download import UrlDownload


def test_url_download_url_filename():
    download = UrlDownload()

    assert download._url_filename('http://example.com') is None
    assert download._url_filename('http://example.com/data') is None
    assert download._url_filename('http://example.com/data.txt') == 'data.txt'
    assert download._url_filename(
        'https://github.com/steinwurf/stub/archive/6.0.0.tar.gz') == \
        '6.0.0.tar.gz'


@vcr.use_cassette('test/vcr_cassettes/https_cxx_prettyprint_resolver.yaml')
def test_url_download_cxx_prettyprint_rename(testdirectory):
    source = 'https://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = testdirectory.path()

    download = UrlDownload()

    path = download.download(cwd=cwd, source=source, filename='test.zip')

    assert os.path.join(cwd, 'test.zip') == path


@vcr.use_cassette('test/vcr_cassettes/https_cxx_prettyprint_resolver.yaml')
def test_url_download_cxx_prettyprin(testdirectory):
    source = 'https://github.com/louisdx/cxx-prettyprint/zipball/master'
    cwd = testdirectory.path()

    download = UrlDownload()

    # Without providing a filename we try to figure out what to call it.
    # In this case it is provided in the Content-Disposition HTTP header.
    # You can open the VCR cassette recording:
    #    test/vcr_cassettes/https_resolver.yaml
    # And you should find the following HTTP header:
    # content-disposition:
    # [attachment; filename=louisdx-cxx-prettyprint-9ab26d2.zip]
    path = download.download(cwd=cwd, source=source)

    assert os.path.join(cwd, 'louisdx-cxx-prettyprint-9ab26d2.zip') == path


@vcr.use_cassette('test/vcr_cassettes/https_stub_resolver.yaml')
def test_url_download_stub_rename(testdirectory):
    source = 'https://github.com/steinwurf/stub/archive/6.0.0.zip'
    cwd = testdirectory.path()

    download = UrlDownload()

    path = download.download(cwd=cwd, source=source, filename='test.zip')

    assert os.path.join(cwd, 'test.zip') == path


@vcr.use_cassette('test/vcr_cassettes/https_stub_resolver.yaml')
def test_url_download_stub(testdirectory):
    source = 'https://github.com/steinwurf/stub/archive/6.0.0.zip'
    cwd = testdirectory.path()

    download = UrlDownload()

    # When the URL contains a filename we expect that to be used.
    path = download.download(cwd=cwd, source=source)

    assert os.path.join(cwd, '6.0.0.zip') == path
