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

class WurfUserResolve(object):
    """
    User Path Resolver functionality. Allows the user to specify the path.
    """

    def __init__(self, options_parser, args, resolver):
        """ Construct an instance.

        :param option_parser: An argparse.ArgumentParser() instance.
        :param args: A list containing the command-line arguments we want to 
            parse.
        :param resolver: The resolver to use if a path option is not available
            in the args list.
        """
        self.options_parser = options_parser
        self.args = args
        self.resolver = resolver
        self.parsed_options = {}

    def __parse_arguement(self, name):
        """ Parse the self.args and see if an --name-path option is present.
        
        If the option is found use that path.
        
        :param name: The name of the dependency we are looking for.
        """

        option = '--%s-path' % name

        if option in self.parsed_options:
            return self.parsed_options[option]

        self.options_parser.add_argument(option, default=None, dest=option)

        known_args, unknown_args = self.options_parser.parse_known_args()

        # Use vars(...) function to convert argparse.Namespace() to dict
        self.parsed_options = vars(known_args)

        return self.parsed_options[option]

    def add_dependency(self, name, **kwargs):
        """ Resolve the path to the dependency.
         
        :param name: The name of the dependency as a string
        :param kwargs: Keyword arguments containing options for the dependency.
        
        :return: The path to the dependency as a string.
        """

        path = self.__parse_arguement(name)
        
        if path:
            return path
        else:
            return self.dependency_manager.add_dependency(
                name=name, **kwargs)

    def __repr__(self):
        """ 
        :return: Representation of this object as a string
        """
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfHashDependency(object):
    def __init__(self, resolver):
        """ Construct an instance.

        :param resolver: The resolver where the depenency options including the 
            computed hash will be forwarded.
        """

        self.resolver = resolver
        
    def add_dependency(self, **kwargs):
        """ Resolve the path to the dependency.
         
        :param kwargs: Keyword arguments containing options for the dependency.
        
        :return: The path to the dependency as a string.
        """
        
        # Make sure the sha1 hash is not already included
        assert('sha1' not in kwargs)

        sha1 = self.__hash_dependency(**kwargs)
        
        return self.resolver.add_dependency(sha1=sha1, **kwargs)

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

class WurfDependencyCache(object):
    def __init__(self, cache, resolver):
        """ Construct an instance.
        
        The dependency cache stores the hash and path of already resolved 
        dependencies. If a dependency is resolved twice the path will be taken
        from the cache.
        
        The cache will have the following "layout":
        
            cache = {'nameX': {'sha1': 'hashX', 'path': '/tmp'},
                     'nameY': {'sha1': 'hashY', 'path': '/tmp'},
                     'nameZ': {'sha1': 'hashZ', 'path': '/tmp'}}
        
        :param cache: Dict object where resolved dependencies will be stored.
        :param resolver: Dependency manager which will do the
            resolve step on cache miss.
        """
        
        self.cache = cache
        self.resolver = resolver
        
    def add_dependency(self, name, sha1, **kwargs):
        """ Resolve the path to the dependency.
         
        :param name: The name of the dependency as a string.
        :param sha1: The hash of the dependency as a string.
        :param kwargs: Keyword arguments containing options for the dependency.
        
        :return: The path to the dependency as a string.
        """
        
        


        sha1 = self.__hash_dependency(**kwargs)
        self.resolver.add_dependency(sha1=sha1, **kwargs)

    def __store_dependency(self, name, config):

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)


    def __skip_dependency(self, name, sha1):
        """ Checks if the depenency is already resolved.
        
        :param name: The name of the dependency as a string.
        :param sha1: The hash of the dependency as a string.

        :return: True if the dependency is already resolved, otherwise False.
        """

        if name not in self.cache:
            return False

        if sha1 == self.cache[name]['sha1']:
            # We already have resolved this dependency
            return True
        else:
            self.ctx.fatal("Mismatch dependency")

    def __repr__(self):
        """ 
        :return: Representation of this object as a string
        """

        return "%s(%r)" % (self.__class__.__name__, self.__dict__)


class WurfFastResolveDependency(object):
    def __init__(self, dependency_manager, bundle_config_path, fast_resolve):
        self.dependency_manager = dependency_manager
        self.bundle_config_path
        self.fast_resolve = fast_resolve
        
        
    def add_dependency(self, name, sha1, **kwargs):
        
        if self.fast_resolve:
            config = self.__load_dependency(name=name, sha1=sha1)
            
        if config and config['sha1'] == sha1:
            return config['path']
            
        return self.dependency_manager.add_dependency(
                name=name, sha1=sha1, **kwargs)
    
    def __load_dependency(self, name):    
            
        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')
            
        if not os.path.isfile(config_path):
            return None
            
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
        
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)



class WurfActiveDependencyManager(object):

    def __init__(self, ctx, bundle_path, bundle_config_path, source_resolver):
        self.ctx = ctx
        self.bundle_path = bundle_path
        self.bundle_config_path = bundle_config_path
        self.source_resolver = source_resolver
        self.dependencies = {}

    def add_dependency(self, **kwargs):
        sha1 = self.__hash_dependency(**kwargs)
        self.__resolve_dependency(sha1=sha1, **kwargs)

    def __resolve_dependency(self, sha1, name, recurse, **kwargs):

        if self.__skip_dependency(name=name, sha1=sha1):
            return

        path = self.__fetch_dependency(name=name, **kwargs)

        # We store the information about the resolve state here.
        # The reason we do it even though we might not have a path is that we
        # want to avoid trying to resolve a dependency that is optional and
        # failed leaving path==None again and again.
        config = {'sha1': sha1, 'path':path}
        self.dependencies[name] = config

        if not path:
            return

        self.__store_dependency(name, config)

        if recurse:
            self.ctx.recurse(path)

    def __store_dependency(self, name, config):

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)


    def __skip_dependency(self, name, sha1):

        if name not in self.dependencies:
            return False

        if sha1 == self.dependencies[name]['sha1']:
            # We already have resolved this dependency
            return True
        else:
            self.ctx.fatal("Mismatch dependency")

    def __fetch_dependency(self, name, optional, **kwargs):

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
                return None
            else:
                raise

        self.ctx.end_msg(path)

        return path


    def __hash_dependency(self, **kwargs):
        s = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha1(s.encode('utf-8')).hexdigest()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
