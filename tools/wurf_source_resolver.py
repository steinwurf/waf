#! /usr/bin/env python
# encoding: utf-8

import argparse

class WurfResolverOptions(object):
    """
    """

    def __init__(self):

        self.parser = argparse.ArgumentParser(description='Resolve Options')

        # Collect the commands, environment variables and arguments that we do
        # not yet understand.
        self.parser.add_argument('args', nargs='*')


        self.options = argparse.Namespace()

    def add_argument(*args, **kwargs):
        parser.add_argument(*args, **kwargs)

    def parse_known_args(args = None):
        self.options = parser.parse_known_args(args)


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)




class WurfGitMethodResolver(object):
    """
    """

    def __init__(self, user_methods, git_methods):
        """ Construct a new WurfSourceResolver instance.

        Args:
            type_resolvers: A dict object mapping source types to resolvers
            instances, providing the resolve(...) function.

                Example:
                    {'checkout': checkout_resolver_instance,
                     'semver': semver_resolver_instance }

            ctx: A Waf Context instance.
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
