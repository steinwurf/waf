#! /usr/bin/env python
# encoding: utf-8

from waflib.Scripting import Dist
from waflib import Options


def options(opt):

    opts = opt.add_option_group("Standalone archive options")

    opts.add_option(
        "--standalone_archive",
        action="store",
        default=None,
        help="Name of the standalone archive",
    )

    opts.add_option(
        "--standalone_algo",
        action="store",
        default="zip",
        help="Compression algorithm of the standalone archive. "
        "Possible values: [zip, tar.bz2, tar.gz]",
    )

    opts.add_option(
        "--standalone_exclude",
        action="store",
        default=None,
        help="Patterns to exclude files from the standalone "
        'archive. (e.g. "*.cache **/*.class")',
    )


class WafStandaloneContext(Dist):

    """creates a standalone archive that contains all dependencies"""

    cmd = "standalone"

    def __init__(self, **kw):
        super(Dist, self).__init__(**kw)

        if Options.options.standalone_archive:
            self.base_name = Options.options.standalone_archive

        self.algo = Options.options.standalone_algo

    def get_files(self):
        excludes = Dist.get_excl(self)
        if Options.options.standalone_exclude:
            # A whitespace separator is needed as the existing excludes
            # string might not end with whitespace
            excludes += " "
            excludes += Options.options.standalone_exclude
        excludes += (
            " waf-* waf3-* .waf-* .waf3-* .lock-* "
            "*.zip *.tar.bz2 *.tar.gz VSProjects *.vcxproj* *.sln "
            "*.sdf *.suo *.bat *.log *.user build resolve_symlinks "
            "resolved_dependencies/*/master"
        )

        return self.base_path.ant_glob("**/*", dir=True, excl=excludes.split())
