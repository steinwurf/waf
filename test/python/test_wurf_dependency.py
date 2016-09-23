import mock

from wurf_dependency import WurfDependency2

def test_wurf_dependency_add_options():

    dependency = WurfDependency2("test")

    opt = mock.Mock()

    resolver = mock.Mock()
    post_resolver = mock.Mock()

    dependency.resolvers.append(resolver)
    dependency.post_resolvers.append(post_resolver)

    dependency.add_options(opt)

    resolver.add_options.assert_called_once_with(opt)
    post_resolver.add_options.assert_called_once_with(opt)


def test_wurf_dependency_resolve():

    dependency = WurfDependency2("test")

    ctx = mock.Mock()
    cwd = '/tmp'

    resolver0 = mock.Mock()
    resolver0.resolve.side_effect = Exception('booom')

    resolver1 = mock.Mock()
    resolver1.resolve.return_value = "/tmp/dir"

    dependency.resolvers.append(resolver0)
    dependency.resolvers.append(resolver1)

    path = dependency.resolve(ctx, cwd)

    assert(path == "/tmp/dir")
