#! /usr/bin/env python
# encoding: utf-8

class WurfSourceResolver(object):
    """
    """

    def __init__(self, source_resolvers, ctx):
        """ Construct a new WurfSourceResolver instance.

        Args:
            source_resolvers: A dict object mapping source types to resolvers
            instances, providing the resolve(...) function.

                Example:
                    {'git': git_resolver_instance,
                     'ftp': ftp_resolver_instance}

            ctx: A Waf Context instance.
        """
        self.source_resolvers = source_resolvers
        self.ctx = ctx

    def resolve(self, name, cwd, sources):

        for source in sources:
            try:
                path = self.__resolve(name, cwd, **source)
            except Exception as e:
                self.ctx.to_log("Source {} resolve failed {}".format(source, e))
            else:
                return path
        else:
            raise RuntimeError("No sources resolved. {}".format(self))


    def __resolve(self, name, cwd, resolver, **kwargs):

        r = self.source_resolvers[resolver]
        return r.resolve(name=name, cwd=cwd, **kwargs)

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

    def __fetch_dependency(self, name, optional, sources):

        self.ctx.start_msg('Resolve dependency {}'.format(name))

        try:
            path = self.source_resolver.resolve(
                name=name, cwd=self.bundle_path, sources=sources)
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
