#! /usr/bin/env python
# encoding: utf-8

import json
import os

class WurfDependency:
    """Defines a dependency.

    A dependency can be many things:

        1. A software library needed.
        2. Resources such as images etc.
        3. Ect.



    """

    def __init__(self, name, resolver, recurse=True, optional=False):

        assert name
        assert resolver

        self.name = name
        self.resolver = resolver

        self.recurse = recurse
        self.optional = optional
        self.path = None

    def resolve(self, ctx):
        """Resolve the dependency.

        :param ctx: Context object used during resolving
        """

        assert ctx.cmd == 'resolve', "Non-resolve context use in resolve step"

        path = ctx.bundle_path()

        resolver_hash = self.resolver.hash()

        # Limit the hash to 8 characters. The reason for this is to avoid a
        # too long folder name for the dependency. But still keep it long
        # enough to minize chances of two names conflicting.
        assert len(resolver_hash) > 0

        if len(resolver_hash) > 8:
            resolver_hash = resolver_hash[:8]

        resolver_path = os.path.join(path, self.name + '-' + resolver_hash)

        if not os.path.exists(resolver_path):

            ctx.to_log(
                "Creating new resolver path: {}".format(resolver_path))
            os.makedirs(resolver_path)

        ctx.start_msg('Resolve dependency %s' % self.name)

        try:
            self.path = self.resolver.resolve(ctx, resolver_path)
        except Exception as e:

            if self.optional:
                # An optional dependency might be unavailable if the user
                # does not have a license to access the repository, so we just
                # print the status message and continue
                ctx.end_msg('Unavailable', color='RED')
            else:
                # Re-raise the exception
                raise
        else:
            ctx.end_msg(self.path)

        if self.path and self.recurse:
            ctx.recurse(self.path)

    def store(self, ctx):
        """Stores information about the dependency."""

        assert self.path,('Cannot store config without a valid path')

        # We typically store configs in the build/ folder of the project
        p = ctx.bundle_config_path()

        if not os.path.exists(p):
            ctx.fatal('Bundle config path not found {} for storing dependency '
                      '{}'.format(p, self.name))

        config_path = os.path.join(p, self.name + '.resolve.json')

        with open(config_path, 'w') as config_file:
            json.dump(self.to_config(), config_file)


    def load(self, ctx):
        """Loads information about the dependency.

        :Args:
            path (string): Path to where information about dependencies are
                stored.

        :Raises:
            Will raise an exception if no information about the dependency
            can be found or if that information is detected out-of-date. In
            which case dependencies should be resolved again.
        """

        # We typically store configs in the build/ folder of the project
        p = ctx.bundle_config_path()

        if not os.path.exists(p):
            ctx.fatal('Bundle config path not found {} for loading dependency '
                      '{}'.format(p, self.name))

        assert self.path == None, ('Dependency {} has a path, '
                                   'in a non-resolve step.'.format(self.name))

        config_path = os.path.join(p, self.name + '.resolve.json')

        if not os.path.isfile(config_path):
            ctx.fatal('Could not load config {} for dependency '
                      '{}'.format(config_path, self.name))

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        if not validate_config(config):
            ctx.fatal('Invalid %s config %s <=> %s'
                      % (self.name, self.config, config))

        if 'path' in config:
            self.path = config['path']


    def validate_config(self, config):
        """Check that the config is valid."""

        # Check that the stored dependency settings match the ones added
        if self.recurse != config['recurse']:
            return False

        if self.optional != config['optional']:
            return False

        if self.resolver.hash() != config['resolver_hash']:
            return False

        if not config.optional and not config.path:
            # The dependency is not optional so it should have a path
            return False

        return True

    def to_config(self):
        """Returns a dict representing the configuration of the dependency."""

        config = {}
        config['recurse'] = self.recurse
        config['optional'] = self.optional
        config['path'] = self.path

        # We also store the hash of the resolver this ensures that we can
        # detect inconsistencies between the potentially downloaded
        # dependency and the resolver.
        #
        # As an example somebody might update the URL of a dependency, in
        # which case we cannot use the stored dependency anymore and need
        # to resolve the dependency again. On the other hand if the
        # resolver hash matches what we stored we know that nothing changed.
        config['resolver_hash'] = self.resolver.hash()

        return config

    def exists(self):
        pass

    def __eq__(self, other):

        if self.name != other.name:
            return False

        if type(self.resolver) != type(other.resolver):
            return False

        if self.config.table != other.config.table:
            return False

        return True
