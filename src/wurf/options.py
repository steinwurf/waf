#! /usr/bin/env python
# encoding: utf-8


class Options(object):

    def __init__(self, args, parser, default_bundle_path,
                 default_symlinks_path, supported_git_protocols):

        self.args = args
        self.parser = parser

        self.known_args = {}
        self.unknown_args = []

        # Using the %default placeholder:
        #    http://stackoverflow.com/a/1254491/1717320
        self.parser.add_argument('--bundle-path',
            default=default_bundle_path,
            dest='--bundle-path',
            help='The folder where the bundled dependencies are downloaded.'
                 '(default: %(default)s)')

        self.parser.add_argument('--git-protocol',
            dest='--git-protocol',
            help='Use a specific git protocol to download dependencies.'
                 'Supported protocols {}'.format(supported_git_protocols))

        self.parser.add_argument('--symlinks-path',
            default=default_symlinks_path,
            dest='--symlinks-path',
            help='The folder where the dependency symlinks are placed.'
                 '(default: %(default)s)')

        self.parser.add_argument('--fast-resolve', dest='--fast-resolve',
            action='store_true', default=False,
            help='Load already resolved dependencies from file system. '
                  'Useful for running configure without resolving dependencies '
                  'again.')

        self.parser.add_argument('--lock_paths', dest='--lock_paths',
            action='store_true', default=False,
            help='Creates the resolve_lock_paths directory which contains the '
                 'paths to all resolved dependencies.')

        self.__parse()

    def bundle_path(self):
        return self.known_args['--bundle-path']

    def symlinks_path(self):
        return self.known_args['--symlinks-path']

    def git_protocol(self):
        return self.known_args['--git-protocol']

    def fast_resolve(self):
        return self.known_args['--fast-resolve']

    def lock_paths(self):
        return self.known_args['--lock_paths']

    def path(self, dependency):
        return self.known_args['--%s-path' % dependency.name]

    def use_checkout(self, dependency):
        return self.known_args['--%s-use-checkout' % dependency.name]

    def __parse(self):

        known, unknown = self.parser.parse_known_args(args=self.args)

        self.known_args = vars(known)
        self.unknown_args = unknown

    def __add_path(self, dependency):

        option = '--%s-path' % dependency.name

        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify path for {}.'.format(
                dependency.name))

    def __add_use_checkout(self, dependency):

        option = '--%s-use-checkout' % dependency.name

        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify Git checkout for {}.'.format(
                dependency.name))

    def add_dependency(self, dependency):

        self.__add_path(dependency)

        if dependency.resolver == 'git':

            self.__add_use_checkout(dependency)

        self.__parse()
