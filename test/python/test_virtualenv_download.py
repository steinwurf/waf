#!/usr/bin/env python
# encoding: utf-8

import os
import mock

from wurf.virtualenv_download import VirtualEnvDownload


def test_virtualenv_download(testdirectory):

    git = mock.Mock()
    ctx = mock.Mock()
    log = mock.Mock()

    downloader = VirtualEnvDownload(
        git=git, ctx=ctx, log=log, download_path=testdirectory.path())

    path = downloader.download()

    assert(path == os.path.join(testdirectory.path(), '15.1.0'))

    git.clone.assert_has_calls([
        mock.call(repository='https://github.com/pypa/virtualenv.git',
                  directory=path, cwd=testdirectory.path())])

    git.checkout.assert_has_calls([
        mock.call(branch='15.1.0', cwd=path)])


def test_virtualenv_download_exists(testdirectory):

    git = mock.Mock()
    ctx = mock.Mock()
    log = mock.Mock()

    clone_dir = testdirectory.mkdir('15.1.0')

    downloader = VirtualEnvDownload(
        git=git, ctx=ctx, log=log, download_path=testdirectory.path())

    path = downloader.download()

    assert(path == clone_dir.path())

    assert not git.clone.called
    assert not git.checkout.called
