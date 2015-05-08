#! /usr/bin/env python
# encoding: utf-8

from waflib.Scripting import Dist
from waflib import Options


def options(opt):

    opts = opt.add_option_group('Standalone archive options')

    opts.add_option('--standalone_archive', action='store', default=None,
                    help='Name of the standalone archive')

    opts.add_option('--standalone_algo', action='store', default='zip',
                    help='Compression algorithm of the standalone archive. '
                         'Possible values: zip, tar.bz2, tar.gz')


class Standalone(Dist):

    '''creates a standalone archive that contains the bundled dependencies'''
    cmd = 'standalone'

    def __init__(self, **kw):
        super(Dist, self).__init__(**kw)

        if Options.options.standalone_archive:
            self.base_name = Options.options.standalone_archive

        self.algo = Options.options.standalone_algo

    def get_files(self):
        excludes = Dist.get_excl(self)
        excludes += ' build **/.git **/.gitignore **/*~ **/*.pyc .lock* ' \
            '*.bat waf-* .waf-* *.zip *.tar.bz2 *.tar.gz VSProjects *.sln '\
            '*.sdf *.suo bundle_dependencies/*/master/*'

        return self.base_path.ant_glob(
            '**/*', dir=True, excl=excludes.split(' '))
