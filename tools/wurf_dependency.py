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
        self._resolver = resolver

        self._recurse = recurse
        self._optional = optional
        self._path = ""


    def resolve(self, ctx):
        """Resolve the dependency.

        Resolving a dependency is fundamentally about finding a path
        where the dependency is available. This may require that we
        e.g. download the dependency or if that is already done simply
        find the path to where it is.
        """

        assert ctx.cmd == 'resolve', "Non-resolve context use in resolve step"

        if ctx.is_active_resolve():
            self._active_resolve(ctx)
        else:
            self._load(ctx)

        if self._optional and not self._path:
            # The dependency is optional and we did manage to get a path,
            # so lets get outta here!
            return

        assert self._path


    def requires_recurse(self):
        """Return True if the dependency should be recursed otherwise False."""
        return self._recurse


    def has_path(self):
        """Return True if the dependency has a path otherwise False."""
        return self._path != ""


    def recurse(self, ctx):
        """Recurse the depedency."""

        assert self.is_recurse()
        assert self.has_path()

        ctx.recurse(self._path)


    def add_options(self, ctx):
        """Add dependency specific options to the options context.

        We never actually parse these options we just put them there
        such that they are available to the user when he/she runs
        e.g. "./waf --help".

        So any options parsed in the dependency during the resolve step
        should be added here.

        The reason for this is that the resolve step for dependencies
        takes place before the options are parsed. Also at the time of
        resolving dependencies we may not know exactly yet which
        dependencies we have as we are iteratively resolving them.
        """

        # If the group already exists we will just get it otherwise it
        # will be created.
        # https://github.com/waf-project/waf/blob/master/waflib/Options.py#L209
        group = ctx.add_option_group('Dependency options')
        group.add_option('--{}-path'.format(self._name),
            dest='{}_dependency'.format(self._name),
            help='Set the path to the dependency')

        # @todo add options for resolver


    def _parse_user_defined_dependency_path(self):
        """The user has specified the dependency path.

        We do not support an optional version of this action. The reason
        is that if the user specifies a path it must exist.

        argparse is used as the parser at this point since it supports
        the parse_known_args(...) function which will only parse what it
        knows. optparse on the other hand will fail if it sees anything
        that looks like an option, but which has not been added as an
        option.

        :return: An empty string if no user defined path was found otherwise
                 it returns a string containing the path.
        """
        p = argparse.ArgumentParser()
        p.add_argument('--{}-path'.format(self._name), dest='dependency_path',
                       default="", type=str)
        args, unknown = p.parse_known_args(args=sys.argv[1:])

        return args.dependency_path


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
                ctx.fatal('Invalid user defined path {}'.format(self._path))

            ctx.end_msg(self._path)

        else:
            self._optional_fetch(ctx)

        self._store(ctx)


    def _optional_fetch(self, ctx):
        """Try to fetch the dependency.

        The optional fetch will attempt to fetch the dependency but if
        it fails it is not a fatal failure.
        """

        ctx.start_msg('Resolve dependency %s' % self._name)

        try:
            self._fetch(ctx)
        except Exception as e:

            ctx.to_log("Exception while fetching dependency: {}".format(e))

            if self._optional:
                # An optional dependency might be unavailable if the user
                # does not have a license to access the repository, so we just
                # print the status message and continue
                ctx.end_msg('Unavailable', color='RED')
            else:
                # Re-raise the exception
                raise
        else:
            ctx.end_msg(self._path)


    def _fetch(self, ctx):
        """Fetch the dependency using the resolver.

        :param ctx: Context object used during resolving
        """

        resolver_path = self._resolver_path(ctx)

        if not os.path.exists(resolver_path):
            ctx.to_log(
                "Creating new resolver path: {}".format(resolver_path))
            os.makedirs(resolver_path)

        self._path = self._resolver.resolve(ctx, resolver_path)


    def _resolver_path(self, ctx):

        resolver_hash = self._resolver.hash()

        # Limit the hash to 8 characters. The reason for this is to avoid a
        # too long folder name for the dependency. But still keep it long
        # enough to minize chances of two names conflicting.
        assert len(resolver_hash) > 0

        if len(resolver_hash) > 8:
            resolver_hash = resolver_hash[:8]

        resolver_path = os.path.join(
            ctx.bundle_path(), self._name + '-' + resolver_hash)

        return resolver_path


    def _store(self, ctx):
        """Store information about the dependency."""

        assert self._optional or os.path.exists(self._path), \
            'Non optional dependencies must have a path'

        config = {
            'name': self._name,
            'path': self._path,
            'optional': self._optional,
            'recurse': self._recurse,
            'resolver_hash': self._resolver.hash()
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

        if self._optional != config['optional']:
            return False

        if self._resolver.hash() != config['resolver_hash']:
            return False

        if not self._optional and not config['path']:
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

        if self._optional != other._optional:
            return False

        if self._resolver.hash() != other._resolver.hash():
            return False

        return True
