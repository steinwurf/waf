import pytest
import mock
import os

from wurf.archive_resolver import ArchiveResolver

def test_archive_resolver(test_directory):

    resolve_path = test_directory.mkdir('resolved')
    resolve_path.write_file('ok.zip', 'foobarbaz')
    resolve_file = os.path.join(resolve_path.path(), 'ok.zip')

    parent_resolver = mock.Mock()
    parent_resolver.resolve = mock.Mock(return_value=resolve_file)

    archive_extract = mock.Mock()

    resolver = ArchiveResolver(archive_extract=archive_extract,
        resolver=parent_resolver, cwd=test_directory.path())

    path = resolver.resolve()

    archive_extract.assert_called_once_with(resolve_file, path)
