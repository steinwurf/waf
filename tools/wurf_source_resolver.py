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


class WurfDependencyResolver(object):
    """
    """

    def __init__(self, source_resolver, log):
        self.source_resolver = source_resolver
        self.log = log

    def resolve(self, dependency, cwd):

        name = dependency['name']
        sources = ['sources']

        try:
            path = self.source_resolver.resolve(
                name=name, cwd=cwd, sources=sources)
        except Exception as e:
            self.log.info("Source {} resolve failed {}".format(source, e))
        else:
            return path



    def __resolve(self, name, cwd, resolver, **kwargs):

        r = self.source_resolvers[resolver]
        return r.resolve(name=name, cwd=cwd, **kwargs)
        
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__dict__)
