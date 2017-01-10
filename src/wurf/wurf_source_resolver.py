#! /usr/bin/env python
# encoding: utf-8

import argparse
import sys


#           +--------------------------+
#           |   WurfHashDependency     |
#           |                          |
#           |   - Hash the dependency  |
#           |     using sha1.          |
#           +--------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#      +-----------------------------------+
#      |   WurfDependencyCache             |
#      |                                   |
#      |   - Cache the path and sha1 for   |
#      |     a resolved dependency.        |
#      |   - Store the path and sha1 in a  |
#      |     persistant cache file.        |
#      |   - Checks that if a dependency   |
#      |     is added twice their sha1     |
#      |     must match.                   |
#      |                                   |
#      +-----------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#     +------------------------------------+
#     |  WurfUserResolve                   |
#     |                                    |
#     |  - Check if user specified a path  |
#     |    on the command-line.            |
#     |                                    |
#     +------------------------------------+
#              +                   ^
#              |                   |
#      add_dependency(...)        path
#              |                   |
#              v                   +
#    +----------------------------------------+
#    |  WurfFastResolve                       |
#    |                                        |
#    |  - Active if the --fast-resolve option |
#    |    is specified.                       |
#    |  - If the cache file exists            |
#    |    loads the path from there.          |
#    |                                        |
#    +----------------------------------------+
#               +                   ^
#               |                   |
#       add_dependency(...)        path
#               |                   |
#               v                   +
#       +---------------------------------+
#       |  WurfResolve                    |
#       |                                 |
#       |  - Uses the specified resolver  |
#       |    type to fetch the dependency |
#       +---------------------------------+




class WurfGitMethodResolver(object):
    """
    """

    def __init__(self, user_methods, git_methods):
        """ Construct an instance.

        :param user_methods: A list of user specified git resolvers. These will
            be tried before using the method.
        :param git_methods: A dict object mapping method types to resolvers
            instances, providing the resolve(...) function.

                Example:
                    {'checkout': checkout_resolver_instance,
                     'semver': semver_resolver_instance }
        """
        self.user_methods = user_methods
        self.git_methods = git_methods

    def resolve(self, name, cwd, source, method, **kwargs):
        """ Resolve the git dependency.

        - First see if the user has provided some options
        - Then use the specified git method

        :param name: Name of the dependency as a string
        :param cwd: Current working directory as a string
        :param source: URL of the git repository as a string
        :param method: The git method to use.
        :param kwargs: Keyword arguments containing options for the dependency

        :return: Path to resolved dependency as a string
        """

        # Try user method
        for m in self.user_methods:
            path = m.resolve(name=name, cwd=cwd, source=source, **kwargs)

            if path:
                return path

        # Use git method
        r = self.git_methods[method]
        return r.resolve(name=name, cwd=cwd, source=source, **kwargs)


    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

from . import wurf_error

class WurfSourceError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self, name, cwd, resolver, sources, **kwargs):

        self.name = name
        self.cwd = cwd
        self.resolver = resolver
        self.sources = sources
        self.kwargs = kwargs

        super(WurfSourceError, self).__init__("Error resolving sources for {}".format(name))



class WurfSourceResolver(object):
    """
    """

    def __init__(self, user_resolvers, type_resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A dict object mapping source types to resolvers
            instances, providing the resolve(...) function.

                Example:
                    {'git': git_resolver_instance,
                     'ftp': ftp_resolver_instance}

        :param ctx: A Waf Context instance.
        """
        self.user_resolvers = user_resolvers
        self.type_resolvers = type_resolvers
        self.ctx = ctx

    def resolve(self, name, cwd, resolver, sources, **kwargs):
        """ Resolve the dependency.

        - First see if the user has provided some options
        - Then use the specified git method

        :param name: Name of the dependency as a string
        :param cwd: Current working directory as a string
        :param resolver: The type of resolver to use.
        :param sources: List of URLs which can be used for the dependency.
        :param kwargs: Keyword arguments containing options for the dependency

        :return: Path to resolved dependency as a string
        """

        # Try user method
        for r in self.user_resolvers:
            path = r.resolve(name=name, cwd=cwd, resolver=resolver,
                sources=sources, **kwargs)

            if path:
                return path

        # Use resolver
        for source in sources:
            try:
                path = self.__resolve(name, cwd, resolver, source, **kwargs)
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    source), exc_info=True)
            else:
                return path
        else:

            msg = "Error resolving sources for {}:\n".format(name)
            msg += "\tcwd={}\n".format(cwd)
            msg += "\tresolver={}\n".format(resolver)
            msg += "\tkwargs={}\n".format(kwargs)
            msg += "\tsources: {}\n".format(sources)

            self.ctx.logger.debug(msg)

            raise WurfSourceError(name=name, cwd=cwd, resolver=resolver,
                sources=sources, **kwargs)


    def __resolve(self, name, cwd, resolver, source, **kwargs):

        r = self.type_resolvers[resolver]
        return r.resolve(name=name, cwd=cwd, source=source, **kwargs)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfSourceResolver2(object):
    """
    """

    def __init__(self, name, resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A list of type resolvers object for the available
           sources

        :param ctx: A Waf Context instance.
        """
        self.name = name
        self.resolvers = resolvers
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
            else:
                assert os.path.isdir(path)
                return path
        else:

            msg = "FAILED RESOLVE SOURCE {} check log for detailed information".format(self.name)
            self.ctx.logger.debug(msg)

            raise RuntimeError(msg)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfSourceResolver2(object):
    """
    """

    def __init__(self, name, resolvers, ctx):
        """ Construct an instance.

        :param user_resolvers: A list of resolvers allowing the user to provide
            the path to a dependency in various ways.

        :param type_resolvers: A list of type resolvers object for the available
           sources

        :param ctx: A Waf Context instance.
        """
        self.name = name
        self.resolvers = resolvers
        self.ctx = ctx

    def resolve(self):
        """ Resolve the dependency.

        :return: Path to resolved dependency as a string
        """

        for resolver in self.resolvers:
            try:
                path = resolver.resolve()
            except Exception as e:

                # Using exc_info will attache the current exception information
                # to the log message (including traceback to where the
                # exception was thrown).
                # Waf is using the standard Python Logger so you can check the
                # docs here (read about the exc_info kwargs):
                # https://docs.python.org/2/library/logging.html
                #
                self.ctx.logger.debug("Source {} resolve failed:".format(
                    resolver), exc_info=True)
            else:
                assert os.path.isdir(path)
                return path
        else:

            msg = "FAILED RESOLVE SOURCE {} check log for detailed information".format(self.name)
            self.ctx.logger.debug(msg)

            raise RuntimeError(msg)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


import os
import hashlib
import json







class WurfBundlePath(object):
    """
    Adds and parses the bundle path option.
    """

    def __init__(self, utils, parser, default_bundle_path, args):
        """ Construct an instance.

        :param utils: The waflib.Utils module
        :param parser: An argparse.ArgumentParser instance.
        :param default_bundle_path: The default bundle path as a string
        :param args: Argument strings as a list, typically this will come
            from sys.argv
        """

        # The next resolver to handle the dependency
        self.next_resolver = None

        # Using the %default placeholder:
        #    http://stackoverflow.com/a/1254491/1717320
        parser.add_argument('--bundle-path',
            default=default_bundle_path,
            dest='bundle_path',
            help='The folder where the bundled dependencies are downloaded.'
                 '(default: %(default)s)')

        known_args, unknown_args = parser.parse_known_args(args=args)

        self.bundle_path = known_args.bundle_path

        # The waflib.Utils.check_dir function will ensure that the directory
        # exists
        utils.check_dir(path=self.bundle_path)

    def add_dependency(self, **kwargs):
        """ Resolve the path to the dependency.

        :param kwargs: Keyword arguments containing options for the dependency.
        """
        self.next_resolver.add_dependency(bundle_path=self.bundle_path,
            **kwargs)


    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfSkipSeenDependency(object):
    def __init__(self, ctx):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        """

        # The next resolver to handle the dependency
        self.next_resolver = None

        # The seen_dependencies dict stores the hash and path of already
        # resolved dependencies. If a dependency is resolved twice the path will
        # be taken from the cache.
        #
        # The dict will have the following "layout":
        #
        #     {'nameX': {'sha1': 'hashX', 'options': {...}},
        #      'nameY': {'sha1': 'hashY', 'options': {...}},
        #      'nameZ': {'sha1': 'hashZ', 'options': {...}}
        self.seen_dependencies = {}

    def add_dependency(self, name, sha1, **kwargs):
        """ Resolve the path to the dependency.

        :param name: Name of the dependency as a string
        :param sha1: Hash of the dependency options as a string
        :param kwargs: Keyword arguments containing options for the dependency.
        """

        if name in self.seen_dependencies:

            seen_sha1 = self.seen_dependencies[name]['sha1']

            if seen_sha1 != sha1:
                seen_options = self.seen_dependencies[name]['options']

                self.ctx.fatal(
                    "SHA1 mismatch adding dependency {} using {} was {}".format(
                    name, kwargs, seen_options))

            # This dependency is already in the cache lets leave
            return

        self.seen_dependencies[name] = {'sha1': sha1, 'options': kwargs}

        self.next_resolver.add_dependency(name=name, sha1=sha1, **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfCacheDependency(object):
    def __init__(self, cache):
        """ Construct an instance.

        Caching the dependency, typically this is the final step in the
        add_dependency(...) chain.

        The dependency cache is used to run Waf commands in resolved
        dependencies.

        The cache will have the following "layout":

            cache = {'nameX': {'recurse': True, 'path': '/tmpX'},
                     'nameY': {'recurse': False, 'path': '/tmpY'},
                     'nameZ': {'recruse': True, 'path': '/tmpZ'}}

        :param cache: Dict object where the resolved dependency meta data will
            be stored.
        """

        # The next resolver to handle the dependency
        self.next_resolver = None
        self.cache = cache

    def add_dependency(self, name, path, recurse, **kwargs):
        """ Resolve the path to the dependency.

        :param name: Name of the dependency as a string
        :param path: Path to the dependency as a string
        :param recurse: Boolean showing whether the dependency should be
            recursed
        :param kwargs: Keyword arguments containing options for the dependency.
        """

        if path:
            config = {'recurse': recurse, 'path': str(path)}
            self.cache[name] = config

        self.next_resolver.add_dependency(name=name, path=path, recurse=recurse,
            **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfRecurseDependency(object):
    def __init__(self, ctx):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        """

        # The next resolver to handle the dependency
        self.next_resolver = None
        self.ctx = ctx

    def add_dependency(self, path, recurse, **kwargs):
        """ Resolve the path to the dependency.
        :param path: Path to the dependency as a string
        :param recurse: Boolean showing whether the dependency should be
            recursed
        :param kwargs: Keyword arguments containing options for the dependency.
        """

        if recurse and path:

            try:
                self.ctx.recurse(path)
            except:
                self.ctx.logger.debug(
                    "Recurse failed path={} recurse={} kwargs={}".format(
                    path, recurse, kwargs), exc_info=True)

                raise

        self.next_resolver.add_dependency(path=path, recurse=recurse, **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfStoreDependency(object):
    def __init__(self, bundle_config_path):
        """ Construct an instance.

        :param resolver: The resolver where the depenency options including the
            computed hash will be forwarded.
        """

        # The next resolver to handle the dependency
        self.next_resolver = None
        self.bundle_config_path = bundle_config_path

    def add_dependency(self, sha1, name, path, **kwargs):
        """ Resolve the path to the dependency.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        config = {'sha1': sha1, 'path':path}

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)

        self.next_resolver.add_dependency(path=path, name=name, sha1=sha1,
            **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfNullResolver(object):

    def add_dependency(self, **kwargs):
        """ Resolve the path to the dependency.

        :param kwargs: Keyword arguments containing options for the dependency.
        """

        pass

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfFastResolveDependency(object):
    def __init__(self, cache, resolver, bundle_config_path, fast_resolve):
        self.dependency_manager = dependency_manager
        self.bundle_config_path
        self.fast_resolve = fast_resolve


    def add_dependency(self, name, sha1, **kwargs):

        if self.fast_resolve:
            config = self.__load_dependency(name=name, sha1=sha1)

        if config and config['sha1'] == sha1:
            self.cache[name] = config
            return

        self.resolver.add_dependency(name=name, sha1=sha1, **kwargs)

    def __load_dependency(self, name):

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        if not os.path.isfile(config_path):
            return None

        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


from . import wurf_dependency

class WurfActiveDependencyResolver(object):

    def __init__(self, ctx, registry):
        self.ctx = ctx
        # The next resolver to handle the dependency
        self.next_resolver = None
        self.registry = registry

    def add_dependency(self, name, optional, **kwargs):

        self.ctx.start_msg('Resolve dependency {}'.format(name))

        del kwargs['sha1']

        dependency = wurf_dependency.WurfDependency(name=name, optional=optional, **kwargs)
        resolver = self.registry.require('dependency_resolver2', dependency=dependency)

        try:
            path = resolver.resolve()

        except Exception as e:

            self.ctx.to_log('Exception while fetching dependency: {}'.format(e))

            if optional:
                # An optional dependency might be unavailable if the user
                # does not have a license to access the repository, so we just
                # print the status message and continue
                self.ctx.end_msg('Unavailable', color='RED')
            else:
                raise

        self.ctx.end_msg(path)

        self.next_resolver.add_dependency(name=name, optional=optional,
            path=path, sha1=dependency.sha1, **kwargs)


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfPassiveDependencyResolver(object):

    def __init__(self, ctx, bundle_config_path):
        self.ctx = ctx
        # The next resolver to handle the dependency
        self.next_resolver = None
        self.bundle_config_path = bundle_config_path

    def __read_config(self, name):
        """ Hash the keyword arguments representing the  to the dependency.

        :return: Hash of the dependency as a string.
        """

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        if not os.path.isfile(config_path):
            self.ctx.fatal('No config - re-run configure')

        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def add_dependency(self, sha1, name, **kwargs):

        config = self.__read_config(name)

        if sha1 != config['sha1']:
            self.ctx.fatal('Failed sha1 check')

        path = str(config['path'])

        # @todo remove
        print("WurfPassiveDependencyResolver path type = {}".format(type(path)))
        print("WurfPassiveDependencyResolver path = {}".format(path))

        self.next_resolver.add_dependency(sha1=sha1, name=name, path=path,
            **kwargs)


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfPassivePathResolverError(wurf_error.WurfError):
    """Generic exception for wurf"""
    def __init__(self):
        super(WurfPassivePathResolverError, self).__init__(
            "No resolving passive paths when using configure")

class WurfPassivePathResolver(object):

    def __init__(self, ctx, name, sha1, active_resolve, bundle_config_path):
        """ Construct an instance.

        :param ctx: A Waf Context instance.
        :param name: Name of the dependency as a string
        :param sha1: Hash of the depenency information as a string
        :param active_resolve: True if we are in an active resolve step
        :param bundle_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        """
        self.ctx = ctx
        self.name = name
        self.sha1 = sha1
        self.active_resolve = active_resolve
        self.bundle_config_path = bundle_config_path

    def __read_config(self):
        """ Read the dependency config from file
        """

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        if not os.path.isfile(config_path):
            self.ctx.fatal('No config - re-run configure')

        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def resolve(self):

        if self.active_resolve:
            raise WurfPassivePathResolverError()

        config = self.__read_config(self.name)

        if self.sha1 != config['sha1']:
            self.ctx.fatal('Failed sha1 check')

        path = str(config['path'])

        if not os.path.is_dir(path):
            self.ctx.fatal('Not valid path {}'.format(path))

        return path


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfOnActiveStorePathResolver(object):

    def __init__(self, resolver, name, sha1, active_resolve, bundle_config_path):
        """ Construct an instance.

        :param resolver: A resolver which will do the actual job
        :param name: Name of the dependency as a string
        :param sha1: Hash of the depenency information as a string
        :param active_resolve: True if we are in an active resolve step
        :param bundle_config_path: A string containing the path to where the
            dependencies config json files should be / is stored.
        """
        self.resolver = resolver
        self.name = name
        self.sha1 = sha1
        self.active_resolve = active_resolve
        self.bundle_config_path = bundle_config_path

    def __write_config(self, path):
        """ Write the dependency config from file
        """

        config_path = os.path.join(
            self.bundle_config_path, self.name + '.resolve.json')

        config = {'sha1': self.sha1, 'path':path}

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)


    def resolve(self):

        path = self.resolver.resolve()

        if self.active_resolve:
            self.__write_config(path=path)

        return path

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfSkipDependencyError(wurf_error.WurfError):
    """Exception raised when a dependency should be skipped."""
    def __init__(self):
        super(WurfPassivePathResolverError, self).__init__(
            "No resolving passive paths when using configure")

class WurfDependencyManager(object):

    def __init__(self, resolver, cache, ctx):
        """ Construct an instance.

        :param steps: List of steps to carry out when adding a dependency.
        """

        self.resolver = resolver
        self.cache = cache
        self.ctx = ctx

        self.seen_dependencies = {}

    def add_dependency(self, **kwargs):

        dependency = wurf_dependency.WurfDependency(**kwargs)

        if self.__skip_dependency(dependency):
            return

        path = self.__resolve_dependency(dependency)

        if not path:
            return

        self.cache[dependency.name] = {'path': path, 'recurse': dependency.recurse}

        if dependency.recurse:
            self.ctx.recurse(path)

    def __skip_dependency(self, dependency):

        if dependency.name in self.seen_dependencies:

            seen_dependency = self.seen_dependencies[dependency.name]

            if seen_dependency.sha1 != dependency.sha1:

                self.ctx.fatal(
                    "SHA1 mismatch adding dependency {} was {}".format(
                    dependency, seen_dependency))

            # This dependency is already in the cache lets leave
            return True

        self.seen_dependencies[name] = dependency

        return False

    def __resolve_dependency(dependency):

        self.ctx.start_msg('Resolve dependency {}'.format(dependency.name))

        try:

            path = self.resolver.resolve()

        except Exception as e:

            self.ctx.to_log('Exception while fetching dependency: {}'.format(e))

            if not dependency.optional:
                raise

            # An optional dependency might be unavailable if the user
            # does not have a license to access the repository, so we just
            # print the status message and continue
            self.ctx.end_msg('Unavailable', color='RED')

        else:
            self.ctx.end_msg(path)

        return path
