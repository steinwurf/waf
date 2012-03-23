#!/usr/bin/env python
# encoding: utf-8

import os

from waflib import Utils
from waflib import Context
from waflib import Options

from waflib.Configure import conf
from waflib.Configure import ConfigurationContext

###############################
# ToolchainConfigurationContext
###############################

class ToolchainConfigurationContext(ConfigurationContext):
    '''configures the project'''
    cmd='configure'

    def init_dirs(self):
        # Waf calls this function to set the output dir.
        # Waf sets the output dir in the following order
        # 1) Check whether the -o option has been specified
        # 2) Check whether the wscript has an out varialble defined
        # 3) Fallback and use the name of the lockfile
        #
        # In order to not suprise anybody we will disallow the out variable
        # but allow our output dir to be overwritten by using the -o option

        assert(getattr(Context.g_module,Context.OUT,None) == None)

        if not Options.options.out:

            # A toolchain was specified use that
            self.out_dir = "build/" + Options.options.toolchain

        super(ToolchainConfigurationContext, self).init_dirs()


##################
# DistcleanContext
##################

def distclean(ctx):
    """
    Since we have nested the toolchain folders in the build dir
    waf does not completly remove it
    """
    import shutil
    import waflib.Scripting as script
    script.distclean(ctx)

    lst = os.listdir('.')

    for k in lst:

        if k == 'build':
            shutil.rmtree('build')


def run_distclean(ctx):
    """
    First we run the one define in the module, then our own one
    """
    Context.g_module.distclean(ctx)
    distclean(ctx)

class DistcleanContext(Context.Context):
    """ Clean the project """
    cmd = 'distclean'
    fun = run_distclean

    def __init__(self, **kw):
        super(DistcleanContext, self).__init__(**kw)

    def execute(self):
        run_distclean(self)



def options(opt):
    toolchain_opts = opt.add_option_group('Toolchain')

    platform = Utils.unversioned_sys_platform()

    toolchain_opts.add_option('--toolchain', default = platform,
                              dest='toolchain',
                              help="Select a specific toolchain "
                                   "[default: %default]"
                                   ", other example --toolchain=android.")

    toolchain_opts.add_option('--toolchain-path', default=None,
                              dest='toolchain_path',
                              help='Set the path to the toolchain')

    opt.load('compiler_cxx')



def platform_toolchain(conf):
    """
    We just select the platform default toolchain. And rely on Waf to detect it
    """

    conf.load('compiler_cxx')


def android_toolchain(conf):
    """
    We wish to use the Android toolchain atm. we use a single setup which we expect
    to work with all Android toolchains however in the future we might have to
    make the choice more specific i.e. android-x86 or similar.
    """
    conf.gxx_common_flags()
    conf.cxx_load_tools()

    if 'TOOLCHAIN_PATH' not in conf.env:
        conf.fatal('android toolchain requires a toolchain path')

    toolchain_dir = conf.env['TOOLCHAIN_PATH']

    toolchain_bin = os.path.join(toolchain_dir, 'bin')

    paths = [toolchain_bin]

    # Setup compiler and linker
    conf.find_program('arm-linux-androideabi-g++', path_list=paths, var='CXX')
    conf.env['LINK_CXX'] = conf.env['CXX']

    conf.find_program('arm-linux-androideabi-gcc', path_list=paths, var='CC')

    #Setup archiver and archiver flags
    conf.find_program('arm-linux-androideabi-ar', path_list=paths, var='AR')
    conf.env['ARFLAGS'] = "rcs"

    #Setup android asm
    conf.find_program('arm-linux-androideabi-as', path_list=paths, var='AS')

    #Setup android nm
    conf.find_program('arm-linux-androideabi-nm', path_list=paths, var='NM')

    #Setup android ld
    conf.find_program('arm-linux-androideabi-ld', path_list=paths, var='LD')

    conf.env['BINDIR'] = os.path.join(toolchain_dir, 'arm-linux-androideabi/bin')

    # Set the andoid define - some libraries rely on this define being present
    conf.env.DEFINES += ['ANDROID']



def configure(conf):

    # Setup the toolchain configure functions
    t = dict()
    platform = Utils.unversioned_sys_platform()

    t[platform] = platform_toolchain
    t['android'] = android_toolchain

    # Check if a specific toolchain should be used
    toolchain = getattr(conf.options, 'toolchain', '')

    # Check if we support the toolchain (empty means default)
    if toolchain not in t:
        conf.fatal('The selected toolchain "%s" is not supported' % toolchain)

    # Store in env
    conf.env['TOOLCHAIN'] = toolchain

    # Check if a specific toolchain should be used
    toolchain_path = getattr(conf.options, 'toolchain_path', None)

    if toolchain_path:
        toolchain_path = os.path.expanduser(toolchain_path)
        toolchain_path = os.path.abspath(toolchain_path)

        conf.msg('Setting toolchain path to:', toolchain_path)

        conf.env['TOOLCHAIN_PATH'] = toolchain_path

    # Get configure function for this toolchain
    function = t[toolchain]

    # Configure
    function(conf)


@conf
def toolchain_cxx_flags(conf):
    """
    Returns the default cxx flags for the choosen toolchain
    """

    # Here one can optionally also switch on the CXX variable
    # to specific the flags for specific compilers
    if conf.env.TOOLCHAIN == 'linux' or conf.env.TOOLCHAIN == 'android':
        return ['-O2', '-g', '-ftree-vectorize', '-Wextra', '-Wall']

    if conf.env['TOOLCHAIN'] == 'win32':
        return ['/O2', '/Ob2', '/W3', '/MD', '/EHs']






