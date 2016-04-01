#! /usr/bin/env python
# encoding: utf-8

import json

class WurfDependency:
    def __init__(self, name, resolver, recurse=True, optional=False):

        self.name = name
        self.resolver = resolver

        self.config = ConfigSet.ConfigSet()
        self.config.recurse = recurse
        self.config.optional = optional
        self.config.resolver_hash = resolver.hash()
        self.config.path = None

    def resolve(self, ctx):
        """Resolve the dependency.

        :param ctx: Context object used during resolving
        """

        path = ctx.dependency_path()

        dependency_hash = resolver.hash()
        dependency_path = os.path.join(path, self.name + '-' + dependency_hash)

        if not os.path.exists(dependency_path):
            ctx.to_log(
                "Creating new dependency path: {}".format(dependency_path))
            os.makedirs(dependency_path)

        self.config.path = resolver.resolve(ctx.dependency_path())

    def store(self, path):
        """Stores information about the dependency."""

        config_path = os.path.join(path, name + '.resolve.py')

        with open(config_path, 'w') as config_file:
            json.dump(self.config, config_file)


    def load(self, path):
        """ Loads information about the dependency."""

        config_path = os.path.join(path, name + '.resolve.py')

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        if not validate_config(config):
            raise Exception('Invalid %s config %s <=> %s'
                                % (self.name, self.config, config))

        self.config = config


    def validate_config(self, config):
        """Check that the config is valid."""

        # Check that the stored dependency settings match the ones added
        if self.config.recurse != config.recurse:
            return False

        if self.config.optional != config.optional:
            return False

        if self.resolver_hash != config.resolver_hash:
            return False

        if not config.optional and not config.path:
            # The dependency is not optional so it should have a path
            return False

        return True


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
