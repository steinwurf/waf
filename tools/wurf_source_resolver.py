#! /usr/bin/env python
# encoding: utf-8

import argparse


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
                self.ctx.to_log("Source {} resolve failed {}".format(source, e))
            else:
                return path
        else:
            raise RuntimeError("No sources resolved. {}".format(self))


    def __resolve(self, name, cwd, resolver, source, **kwargs):

        r = self.type_resolvers[resolver]
        return r.resolve(name=name, cwd=cwd, source=source, **kwargs)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


import os
import hashlib
import json




class WurfHashDependency(object):
    def __init__(self, next_resolver):
        """ Construct an instance.

        :param next_resolver: The resolver where the depenency options including the
            computed hash will be forwarded.
        """
        self.next_resolver = next_resolver

    def add_dependency(self, **kwargs):
        """ Resolve the path to the dependency.

        :param kwargs: Keyword arguments containing options for the dependency.

        :return: The path to the dependency as a string.
        """

        # Make sure the sha1 hash is not already included
        assert('sha1' not in kwargs)

        sha1 = self.__hash_dependency(**kwargs)

        self.next_resolver.add_dependency(sha1=sha1, **kwargs)

    def __hash_dependency(self, **kwargs):
        """ Hash the keyword arguments representing the  to the dependency.

        :return: Hash of the dependency as a string.
        """

        s = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha1(s.encode('utf-8')).hexdigest()

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfSkipSeenDependency(object):
    def __init__(self, next_resolver, ctx):
        """ Construct an instance.

        :param next_resolver: The resolver where the depenency options including
            the computed hash will be forwarded.
        :param ctx: A Waf Context instance.
        """
        self.next_resolver = next_resolver

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
    def __init__(self, next_resolver, cache):
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

        self.next_resolver = next_resolver
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
            config = {'recurse': recurse, 'path': path,}
            self.cache[name] = config

        self.next_resolver.add_dependency(name=name, path=path, recurse=recurse,
            **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfRecurseDependency(object):
    def __init__(self, next_resolver, ctx):
        """ Construct an instance.

        :param next_resolver: The resolver where the depenency options including the
            computed hash will be forwarded.
        :param ctx: A Waf Context instance.
        """

        self.next_resolver = next_resolver
        self.ctx = ctx

    def add_dependency(self, path, recurse, **kwargs):
        """ Resolve the path to the dependency.
        :param path: Path to the dependency as a string
        :param recurse: Boolean showing whether the dependency should be
            recursed
        :param kwargs: Keyword arguments containing options for the dependency.
        """

        if recurse and path:
            self.ctx.recurse(path)

        self.next_resolver.add_dependency(path=path, recurse=recurse, **kwargs)

    def __repr__(self):
        """
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)

class WurfStoreDependency(object):
    def __init__(self, next_resolver, bundle_config_path):
        """ Construct an instance.

        :param resolver: The resolver where the depenency options including the
            computed hash will be forwarded.
        """

        self.next_resolver = next_resolver
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



class WurfActiveDependencyResolver(object):

    def __init__(self, ctx, bundle_path, next_resolver, source_resolver):
        self.ctx = ctx
        self.bundle_path = bundle_path
        self.next_resolver = next_resolver
        self.source_resolver = source_resolver

    def add_dependency(self, name, optional, **kwargs):

        self.ctx.start_msg('Resolve dependency {}'.format(name))

        try:
            path = self.source_resolver.resolve(
                name=name, cwd=self.bundle_path, **kwargs)

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
            path=path, **kwargs)


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfPassiveDependencyResolver(object):

    def __init__(self, ctx, next_resolver, bundle_config_path):
        self.ctx = ctx
        self.next_resolver = next_resolver
        self.bundle_config_path = bundle_config_path

    def __read_config(self, name):
        """ Hash the keyword arguments representing the  to the dependency.

        :return: Hash of the dependency as a string.
        """

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        if not os.path.isfile(config_path):
            ctx.fatal('No config - re-run configure')

        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def add_dependency(self, sha1, name, **kwargs):

        config = self.__read_config(name)

        if sha1 != config['sha1']:
            ctx.fatal('Failed sha1 check')

        path = config['path']

        self.next_resolver.add_dependency(sha1=sha1, name=name, path=path,
            **kwargs)


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)