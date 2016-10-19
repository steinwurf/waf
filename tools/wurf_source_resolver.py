#! /usr/bin/env python
# encoding: utf-8

class WurfSourceResolver(object):
    """
    """

    def __init__(self, source_resolvers, log):
        self.source_resolvers = source_resolvers
        self.log = log

    def resolve(self, name, cwd, sources):

        for source in sources:
            try:
                path = self.__resolve(name, cwd, **source)
            except Exception as e:
                self.log.info("Source {} resolve failed {}".format(source, e))
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

        sha1 = self.hash_dependency(**kwargs)
        self.__add_dependency(sha1=sha1, **kwargs)

    def __add_dependency(self, sha1, name, optional, recurse, sources):

        if name in self.dependencies:

            if sha1 == self.dependencies[name]:
                # We already have resolved this dependency
                return
            else:
                self.ctx.fatal("Mismatch dependency")

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
                return
            else:
                raise

        self.ctx.end_msg(path)

        config_path = os.path.join(
            self.bundle_config_path, name + '.resolve.json')

        config = {'sha1': sha1, 'path':path}

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)

        self.dependencies[name] = sha1


    def hash_dependency(self, **kwargs):
        s = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha1(s.encode('utf-8')).hexdigest()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
