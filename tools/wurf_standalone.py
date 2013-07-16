#! /usr/bin/env python
# encoding: utf-8

from waflib.Scripting import Dist
from waflib import Options

def options(opt):

    opt.add_option('--standalone_archive', action='store', default = None,
                   help = 'Name of the standalone archive '
                          'e.g. test_archive')

    opt.add_option('--standalone_algo', action='store', default = 'zip',
                   help = 'valid algo types are tar.bz2, tar.gz or zip')


class Standalone(Dist):

    cmd = 'standalone'

    def __init__(self, **kw):
        super(Dist, self).__init__(**kw)

        if Options.options.standalone_archive:
            self.base_name = Options.options.standalone_archive

        self.algo = Options.options.standalone_algo

    def get_excl(self):
        excl = super(Standalone, self).get_excl()
        excl += 'build **/.git **/.gitignore **/*~ **/*.pyc .lock* *.bat ' \
                'waf-* .waf-* *.zip *.tar.bz2 *.tar.gz '\
                'bundle_dependencies/*/master/*'

        return excl

def standalone(ctx):
        '''makes a tarball for redistributing the sources'''
        pass
