#! /usr/bin/env python
# encoding: utf-8

import json
import os
import argparse
import sys

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

        self._name = name
        self.resolver = resolver

        self._recurse = recurse
        self.optional = optional
        self._path = ""


    def resolve(self, ctx):

        assert ctx.cmd == 'resolve', "Non-resolve context use in resolve step"

        if ctx.is_active_resolve():
            self._active_resolve(ctx)
        else:
            self._load(ctx)

        if self.optional and not self._path:
            # The dependency is optional and we did manage to get a path,
            # so lets get outta here!
            return

        assert self._path

    def is_recurse(self):
        return self._recurse

    def has_path(self):
        return self._path != ""

    def recurse(self, ctx):

        assert self.is_recurse()
        assert self.has_path()

        ctx.recurse(self._path)

    def _active_resolve(self, ctx):
        """Actively resolve the dependency.

        This function chooses the "active" resolve action. In case of
        later extension this would be the place to add in support for
        further resolve actions.
        """

        self._path = self._parse_user_defined_dependency_path()

        if self._path:

            ctx.start_msg('User resolve dependency %s' % self._name)

            if not os.path.exists(self._path):
                ctx.fatal('FAAAAAAAAAIIILL')

            ctx.end_msg(self._path)

        else:
            self.optional_fetch(ctx)

        self.store(ctx)

    def add_options(self, ctx):
        pass

    def _parse_user_defined_dependency_path(self):
        """The user has specified the dependency path.

        We do not support an optional version of this action. The reason
        is that if the user specifies a path it must exist.
        """
        p = argparse.ArgumentParser()
        p.add_argument('--%s-path' % self._name, dest='dependency_path',
                       default="", type=str)
        args, unknown = p.parse_known_args(args=sys.argv[1:])

        return args.dependency_path

    def has_user_defined_dependency_path(self, name):

        return self.user_defined_dependency_path(name)



        ctx.start_msg('User resolve dependency %s' % self._name)
        self._path = ctx.user_defined_dependency_path(ctx)

        if not os.path.exists(self._path):
            ctx.fatal('FAAAAAAAAAIIILL')

        ctx.end_msg(self._path)


    def optional_fetch(self, ctx):
        """Try to fetch the dependency. If dependency is optional allow failure.
        """

        ctx.start_msg('Resolve dependency %s' % self._name)

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
            ctx.end_msg(self._path)


    def fetch(self, ctx):
        """Fetch the dependency using the resolver.

        :param ctx: Context object used during resolving
        """

        resolver_path = self.resolver_path(ctx)

        if not os.path.exists(resolver_path):
            ctx.to_log(
                "Creating new resolver path: {}".format(resolver_path))
            os.makedirs(resolver_path)

        self._path = self.resolver.resolve(ctx, resolver_path)


    def resolver_path(self, ctx):

        resolver_hash = self.resolver.hash()

        # Limit the hash to 8 characters. The reason for this is to avoid a
        # too long folder name for the dependency. But still keep it long
        # enough to minize chances of two names conflicting.
        assert len(resolver_hash) > 0

        if len(resolver_hash) > 8:
            resolver_hash = resolver_hash[:8]

        resolver_path = os.path.join(
            ctx.bundle_path(), self._name + '-' + resolver_hash)

        return resolver_path


    def store(self, ctx):
        """Store information about the dependency."""

        assert self.optional or os.path.exists(self._path), \
            'Non optional dependencies must have a path'

        config = {
            'name': self._name,
            'path': self._path,
            'optional': self.optional,
            'recurse': self._recurse,
            'resolver_hash': self.resolver.hash()
            }

        # We typically store configs in the build/ folder of the project
        p = ctx.bundle_config_path()

        assert os.path.exists(p), \
            'Bundle config path not found {} for storing dependency '\
            '{}'.format(p, self._name)

        config_path = os.path.join(p, self._name + '.resolve.json')

        with open(config_path, 'w') as config_file:
            json.dump(config, config_file)


    def _load(self, ctx):
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
            '{}'.format(p, self._name)

        assert not self._path, \
            'Dependency {} has path, in a non-resolve step.'.format(self._name)

        config_path = os.path.join(p, self._name + '.resolve.json')

        if not os.path.isfile(config_path):
            ctx.fatal('Could not load config {} for dependency '
                      '{}'.format(config_path, self._name))

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        try:
            self._validate_config(config)
        except:
            ctx.fatal('Invalid %s config %s.'.format(self._name, config))
        else:
            self._path = config['path']


    def _validate_config(self, config):
        """Check that the config is valid."""

        # Check that the stored dependency settings match the ones added
        if self._name != config['name']:
            return False

        if self._recurse != config['recurse']:
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


    def __eq__(self, other):

        if self._name != other._name:
            return False

        if self._recurse != other._recurse:
            return False

        if self.optional != other.optional:
            return False

        if self.resolver.hash() != other.resolver.hash():
            return False

        return True
