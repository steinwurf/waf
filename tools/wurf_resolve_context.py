#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import argparse

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs
from waflib import ConfigSet
from waflib import Node

from wurf_dependency import WurfDependency


# To create the tree. https://gist.github.com/hrldcpr/2012250

dependencies = dict()
"""Dictionary that stores the dependencies resolved.

The dictionary will be initialized by the WurfResolveContext and can be
used by all other contexts or tools that need to access the
dependencies. The idea is that this will be the single place to look to
figure out which dependencies exist.
"""

def recurse_dependencies(ctx):

    for name, dependency in dependencies.items():

        ctx.to_log("Recurse dependency {}".format(name))

        if dependency.has_path() and dependency.requires_recurse():

            ctx.to_log("Recurse for {}: cmd={}, path={}".format(
                name, ctx.cmd, dependency.path()))

            ctx.recurse(dependency.path())

        if ctx.cmd == 'options':
            dependency.add_options(ctx)


class WurfResolveContext(Context.Context):

    '''resolves the dependencies specified in the wscript's resolve function'''

    cmd = 'resolve'
    fun = 'resolve'

    def __init__(self, **kw):
        super(WurfResolveContext, self).__init__(**kw)

    def execute(self):

        # Create the nodes that will be used during the resolve step
        self.bldnode = self.path.make_node('build')
        self.bldnode.mkdir()

        # Create a log file if this is an "active" resolve step
        path = os.path.join(self.bldnode.abspath(), 'resolve.log')
        self.logger = Logs.make_logger(path, 'cfg')

        # Directly call Context.execute() to avoid the side effects of
        # ConfigurationContext.execute()
        super(WurfResolveContext, self).execute()


    def bundle_config_path(self):
        """Returns the bundle config path.

        The bundle config path will be used to store/load configuration for
        the different dependencies that are resolved.
        """

        return self.bldnode.abspath()

    def bundle_path(self):
        """Returns the bundle path.

        The bundle path is used by the different resolvers to download
        the dependencies i.e. it represents the path in the file system
        where all bundled dependencies are stored.
        """
        return os.path.join(self.path.abspath(), 'bundle_dependencies')

    def is_active_resolve(self):

        show_help = '-h' in sys.argv or '--help' in sys.argv

        # If active_resolvers is true, then the dependency resolvers are
        # allowed to download the dependencies. If it is false, then the
        # dependency bundle will only recurse into the previously resolved
        # dependencies to fetch the options from these.
        return 'configure' in sys.argv and not show_help

    def user_defined_dependency_path(self, name):

        p = argparse.ArgumentParser()
        p.add_argument('--%s-path' % name, dest='dependency_path',
                       default="", type=str)
        args, unknown = p.parse_known_args(args=sys.argv[1:])

        return args.dependency_path

    def has_user_defined_dependency_path(self, name):

        return self.user_defined_dependency_path(name)


    def add_dependency(self, name, resolver, recurse=True, optional=False):
        """Adds a dependency.

        :param name: The name of the dependency. Must be unique.

        :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
        :param recursive_resolve: specifies if it is allowed to recurse into the
        dependency wscript after the dependency is resolved
        :param optional: specifies if this dependency is optional (an optional
                     dependency might not be resolved if unavailable)
        """

        dependency = WurfDependency(name, resolver, recurse, optional)

        if name in dependencies:
            # The dependency already exists lets check that these are
            # compatible. If they are we have nothing else to do since it
            # should have been resolved.

            if dependency != dependencies[name]:
                ctx.fatal('Incompatible dependencies with same name %r <=> %r'
                            % (dependency, dependencies[name]))
            else:
                return

        dependency.resolve(self)

        if dependency.has_path() and dependency.requires_recurse():

            self.to_log("Recurse for {}: cmd={}, path={}".format(
                name, self.cmd, dependency.path()))

            self.recurse(dependency.path())

        dependencies[name] = dependency
