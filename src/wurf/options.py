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
        self.parser.add_argument('--bundle_path',
            default=default_bundle_path,
            dest='--bundle_path',
            help='The folder where the bundled dependencies are downloaded.'
                 '(default: %(default)s)')

        self.parser.add_argument('--git_protocol',
            dest='--git_protocol',
            help='Use a specific git protocol to download dependencies.'
                 'Supported protocols {}'.format(supported_git_protocols))

        self.parser.add_argument('--symlinks_path',
            default=default_symlinks_path,
            dest='--symlinks_path',
            help='The folder where the dependency symlinks are placed.'
                 '(default: %(default)s)')

        self.parser.add_argument('--fast_resolve', dest='--fast_resolve',
            action='store_true', default=False,
            help='Load already resolved dependencies from file system. '
                  'Useful for running configure without resolving dependencies '
                  'again.')

        self.__parse()

    def bundle_path(self):
        return self.known_args['--bundle_path']

    def symlinks_path(self):
        return self.known_args['--symlinks_path']

    def git_protocol(self):
        return self.known_args['--git_protocol']

    def fast_resolve(self):
        return self.known_args['--fast_resolve']

    def path(self, dependency):
        return self.known_args['--%s_path' % dependency.name]

    def checkout(self, dependency):
        return self.known_args['--%s_checkout' % dependency.name]

    def __parse(self):

        known, unknown = self.parser.parse_known_args(args=self.args)

        self.known_args = vars(known)
        self.unknown_args = unknown

    def __add_path(self, dependency):

        option = '--%s_path' % dependency.name

        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify path for {}.'.format(
                dependency.name))

    def __add_checkout(self, dependency):

        option = '--%s_checkout' % dependency.name

        self.parser.add_argument(option,
            nargs='?',
            dest=option,
            help='Manually specify Git checkout for {}.'.format(
                dependency.name))

    def add_dependency(self, dependency):

        self.__add_path(dependency)

        if dependency.resolver == 'git':

            self.__add_checkout(dependency)

        self.__parse()
