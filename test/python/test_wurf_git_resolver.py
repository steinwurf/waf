import pytest
import mock
import os

# from wurf_git_resolver import WurfGitSResolver
#
# def test_wurf_git_resolver(test_directory):
#
#     resolver = WurfGitSResolver(name='links',
#                                 url='gitlab.com/steinwurf/links.git',
#                                 log=mock.Mock())
#
#     ctx = mock.Mock()
#     ctx.git_default_scheme.return_value=None
#
#     cwd = test_directory.path()
#
#     path = resolver.resolve(ctx, cwd)
#
#     # Given  /tmp/test_wurf_git_resolver0/links-master-04aeea yields:
#     #
#     #    links-master-04aeea
#     #
#     # The destination is computed in the resolve function we just get it here
#     # manually.
#     destination = os.path.basename(os.path.normpath(path))
#
#     ctx.git_clone.assert_called_once_with(
#         source='https://gitlab.com/steinwurf/links.git',
#         destination=destination,
#         cwd=cwd)
#
#     ctx.git_get_submodules.assert_called_once_with(repository_dir=path)
#
#     # Lets try to create the destination folder and check if we just pull
#     test_directory.mkdir(destination)
#
#     # Reset our context
#     ctx = mock.Mock()
#     ctx.git_default_scheme.return_value=None
#
#     path = resolver.resolve(ctx, cwd)
#
#     ctx.git_pull.assert_called_once_with(cwd=path)
#     ctx.git_get_submodules.assert_called_once_with(repository_dir=path)
