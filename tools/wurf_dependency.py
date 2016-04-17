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

    Error handling policy: In the following code we will use two
    approaches to deal with errors either we will use an assert or we
    will call ctx.fatal. The reason for using on or the other is the following:

    If the cause of the error should have been checked somewhere else we
    use an assert if the error cannot be checked elsewhere we use ctx.fatal.

    Note on unit tests: We will in the unit tests not test conditions
    that lead to assertion errors.
    """

    def __init__(self, name, resolver, recurse=True, optional=False):
        """Creates a new WurfDependency object.



        """
        assert name
        assert resolver

        self.name = name
        self.resolver = resolver

        self.recurse = recurse
        self.optional = optional
        self.path = ""


    def resolve(self, ctx):

        assert ctx.cmd == 'resolve', "Non-resolve context use in resolve step"

        if ctx.is_active_resolve():
            self.active_resolve(ctx)
        else:
            self.load(ctx)

        if self.optional and not self.path:
            # The dependency is optional and we did manage to get a path,
            # so lets get outta here!
            return

        assert self.path

        if self.recurse:
            ctx.recurse(self.path)


    def active_resolve(self, ctx):
        """Actively resolve the dependency.

        This function chooses the "active" resolve action. In case of
        later extension this would be the place to add in support for
        further resolve actions.
        """

        if ctx.has_user_defined_dependency_path(self.name):
            self.user_defined_dependency_path(ctx)

        else:
            self.optional_fetch(ctx)

        self.store(ctx)


    def user_defined_dependency_path(self, ctx):
        """The user has specified the dependency path.

        We do not support an optional version of this action. The reason
        is that if the user specifies a path it must exist.
        """
        ctx.start_msg('User resolve dependency %s' % self.name)
        self.path = ctx.user_defined_dependency_path(ctx)

        if not os.path.exists(self.path):
            ctx.fatal('FAAAAAAAAAIIILL')

        ctx.end_msg(self.path)


    def optional_fetch(self, ctx):
        """Try to fetch the dependency. If dependency is optional allow failure.
        """

        ctx.start_msg('Resolve dependency %s' % self.name)

        try:
            self.fetch(ctx)
        except Exception as e:

            ctx.to_log("Exception while fetching dependency: {}".format(e))

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


    def fetch(self, ctx):
        """Fetch the dependency using the resolver.

        :param ctx: Context object used during resolving
        """

        resolver_path = self.resolver_path(ctx)

        if not os.path.exists(resolver_path):
            ctx.to_log(
                "Creating new resolver path: {}".format(resolver_path))
            os.makedirs(resolver_path)

        self.path = self.resolver.resolve(ctx, resolver_path)


    def resolver_path(self, ctx):

        resolver_hash = self.resolver.hash()

        # Limit the hash to 8 characters. The reason for this is to avoid a
        # too long folder name for the dependency. But still keep it long
        # enough to minize chances of two names conflicting.
        assert len(resolver_hash) > 0

        if len(resolver_hash) > 8:
            resolver_hash = resolver_hash[:8]

        resolver_path = os.path.join(
            ctx.bundle_path(), self.name + '-' + resolver_hash)

        return resolver_path


    def store(self, ctx):
        """Store information about the dependency."""

        assert self.optional or os.path.exists(self.path), \
            'Non optional dependencies must have a path'

        config = {
            'name': self.name,
            'path': self.path,
            'optional': self.optional,
            'recurse': self.recurse,
            'resolver_hash': self.resolver.hash()
            }

        # We typically store configs in the build/ folder of the project
        p = ctx.bundle_config_path()

        assert os.path.exists(p), \
            'Bundle config path not found {} for storing dependency '\
            '{}'.format(p, self.name)

        config_path = os.path.join(p, self.name + '.resolve.json')

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)


    def load(self, ctx):
        """Load information about the dependency.

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

        assert os.path.exists(p), \
            'Bundle config path not found {} for loading dependency '\
            '{}'.format(p, self.name)

        assert not self.path, \
            'Dependency {} has path, in a non-resolve step.'.format(self.name)

        config_path = os.path.join(p, self.name + '.resolve.json')

        if not os.path.isfile(config_path):
            ctx.fatal('Could not load config {} for dependency '
                      '{}'.format(config_path, self.name))

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        if not self.validate_config(config):
            ctx.fatal('Invalid %s config %s.'.format(self.name, config))

        if 'path' in config:
            self.path = config['path']


    def validate_config(self, config):
        """Check that the config is valid."""

        # Check that the correct keys are present

        if not 'name' in config:
            return False

        if not 'recurse' in config:
            return False

        if not 'optional' in config:
            return False

        if not 'resolver_hash' in config:
            return False

        if not 'path' in config:
            return False

        # Check that the stored dependency settings match the ones added
        if self.name != config['name']:
            return False

        if self.recurse != config['recurse']:
            return False

        if self.optional != config['optional']:
            return False

        if self.resolver.hash() != config['resolver_hash']:
            return False

        if not self.optional and not config['path']:
            # The dependency is not optional so it should have a path
            return False

        if config['path'] and not os.path.exists(config['path']):
            # If a path is specified it should also exist in the file
            # system
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
