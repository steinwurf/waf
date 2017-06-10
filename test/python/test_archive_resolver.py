import mock
import os

from wurf.archive_resolver import ArchiveResolver


def test_archive_resolver(testdirectory):

    resolve_path = testdirectory.mkdir('resolved')
    resolve_path.write_binary('ok.zip', b'foobarbaz')
    resolve_file = os.path.join(resolve_path.path(), 'ok.zip')

    parent_resolver = mock.Mock()
    parent_resolver.resolve = mock.Mock(return_value=resolve_file)

    archive_extractor = mock.Mock()

    resolver = ArchiveResolver(archive_extractor=archive_extractor,
                               resolver=parent_resolver,
                               cwd=testdirectory.path())

    path = resolver.resolve()

    archive_extractor.assert_called_once_with(path=resolve_file, to_path=path)
