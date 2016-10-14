import pytest
import mock

# from wurf_dependency import WurfDependency2
#
# def test_wurf_dependency_add_options():
#
#     log = mock.Mock()
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     opt = mock.Mock()
#
#     resolver = mock.Mock()
#     post_resolver = mock.Mock()
#
#     dependency.resolvers.append(resolver)
#     dependency.post_resolvers.append(post_resolver)
#
#     dependency.add_options(opt)
#
#     resolver.add_options.assert_called_once_with(opt)
#     post_resolver.add_options.assert_called_once_with(opt)
#
# def test_wurf_dependency_resolve_no_resolvers():
#     """
#     Tests that an exception is raised if there are no resolvers.
#     """
#
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     ctx = mock.Mock()
#     cwd = '/tmp'
#
#     with pytest.raises(Exception):
#         path = dependency.resolve(ctx, cwd)
#
#
# def test_wurf_dependency_resolve_success():
#     """
#     Tests that everything works if a resolver succeeds
#     """
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     ctx = mock.Mock()
#     cwd = '/tmp'
#
#     resolver0 = mock.Mock()
#     resolver0.resolve.side_effect = Exception('booom')
#
#     resolver1 = mock.Mock()
#     resolver1.resolve.return_value = "/tmp/dir"
#
#     dependency.resolvers.append(resolver0)
#     dependency.resolvers.append(resolver1)
#
#     path = dependency.resolve(ctx, cwd)
#
#     assert(path == "/tmp/dir")
#
#
# def test_wurf_dependency_resolve_failure():
#     """
#     Tests that an exception is thrown if no resolvers work
#     """
#
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     ctx = mock.Mock()
#     cwd = '/tmp'
#
#     resolver0 = mock.Mock()
#     resolver0.resolve.side_effect = Exception('booom')
#
#     resolver1 = mock.Mock()
#     resolver0.resolve.side_effect = Exception('booom')
#
#     with pytest.raises(Exception):
#         path = dependency.resolve(ctx, cwd)
#
#
# def test_wurf_dependency_post_resolve():
#     """
#     Tests that post resolvers are invoked and that directories are propagated
#     properly.
#     """
#
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     ctx = mock.Mock()
#     cwd = '/tmp'
#
#     resolver0 = mock.Mock()
#     resolver0.resolve.return_value = "/tmp/dir"
#
#     post_resolver0 = mock.Mock()
#     post_resolver0.resolve.return_value = "/tmp/dir1"
#
#     post_resolver1 = mock.Mock()
#     post_resolver1.resolve.return_value = "/tmp/dir2"
#
#     dependency.resolvers.append(resolver0)
#
#     dependency.post_resolvers.append(post_resolver0)
#     dependency.post_resolvers.append(post_resolver1)
#
#     path = dependency.resolve(ctx, cwd)
#
#     assert(path == "/tmp/dir2")
#
#     resolver0.resolve.assert_called_once_with(ctx, cwd)
#     post_resolver0.resolve.assert_called_once_with(ctx, cwd, "/tmp/dir")
#     post_resolver1.resolve.assert_called_once_with(ctx, cwd, "/tmp/dir1")
#
#
# def test_wurf_dependency_resolve_add_options():
#     """
#     Tests that add_options is called on both resolvers and post_resolvers
#     """
#
#     dependency = WurfDependency2(name="test", log=mock.Mock())
#
#     opt = mock.Mock()
#
#     resolver = mock.Mock()
#     post_resolver = mock.Mock()
#
#     dependency.resolvers.append(resolver)
#     dependency.post_resolvers.append(post_resolver)
#
#     dependency.add_options(opt)
#
#     resolver.add_options.assert_called_once_with(opt)
#     post_resolver.add_options.assert_called_once_with(opt)
