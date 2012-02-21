#! /usr/bin/env python
# encoding: utf-8

from waflib.Configure import conf
from waflib.Configure import ConfigurationContext
from waflib.Options import OptionsContext
from waflib.ConfigSet import ConfigSet

import waflib.Options as Opt

from waflib import Logs
from waflib import Options
from waflib import Utils
from waflib import Scripting
from waflib import Context
from waflib import Errors

import sys
import os
import shutil




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


###############################
# DependencyOptionsContext etc.
###############################

dependencies = dict()
dependency_config = ConfigSet()

options_dirty = False

DEPENDENCY_FILE = '.dependency_config'
""" The config file which tracks which dependencies have been choosen """

RECURSE_DEPENDENCY = 0
""" The dependency wscript should be recursed """

CHECK_DEPENDENCY = 1
""" The dependency should be checked only """

OPTIONS_NAME = 'Dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """ 

DEP_PATH_DEST = 'depend_%s_path'
""" Destination of the dependency paths in the options """

WURFTOOL_VERSION = 'v0.1.0'
"""
The version of this tool bump this version on changes to allow users to see
exactly which version they are using.
"""

WURFTOOL_ABI_VERSION = 'v0.1.1'
"""
The version of layout of the DEPENDENCY_FILE,
bumpt this version if you make incompatible changes
"""

#################################
# Load the wurftools dependencies
#################################

def load_dependency_config():
    """
    Loads dependencies from the config file
    """
    global dependency_config
    
    try:
        dependency_config.load(DEPENDENCY_FILE)
    except Exception:
        pass

    if dependency_config.ABI != WURFTOOL_ABI_VERSION:
        dependency_config = ConfigSet()

    if not dependency_config.ABI:
        dependency_config.ABI = WURFTOOL_ABI_VERSION

    if not dependency_config.BUNDLE:
        dependency_config.BUNDLE = ['NONE']

    if not dependency_config.BUNDLE_PATH:
        dependency_config.BUNDLE_PATH = os.path.abspath(DEFAULT_BUNDLE_PATH)

def store_dependency_config():
    """
    Stores the dependency config
    """
    dependency_config.store(DEPENDENCY_FILE)


def options(opt):
    opt.load('toolchain_cxx')
    opt.load('git')

def configure(conf):
    conf.load('toolchain_cxx')
    conf.load('git')

    load_dependency_config()
    dependency_config['GIT'] = conf.env['GIT']
    store_dependency_config()

def is_system_dependency_impl(name):
    """
    Returns true if the dependency has been specified
    """
    if name not in dependencies:
        self.fatal('%s not recognized as an added dependency' % name)

    if name in dependency_config['BUNDLE']:
        return False

    if dependency_config[DEP_PATH_DEST % name]:
        return False

    return True


class DependencyOptionsContext(OptionsContext):

    

    def __init__(self, **kw):
        """
        Constructor for the dependency options
        """
        
        super(DependencyOptionsContext, self).__init__(**kw)

        load_dependency_config()
        self.add_dependency_options()
        self.preprocess_dependency_options()
        store_dependency_config()


    def add_dependency_options(self):
        """
        Adds the options needed to control dependencies to the
        options context
        """

        bundle_opts = self.add_option_group(OPTIONS_NAME)

        add = bundle_opts.add_option

        add('--bundle', default=False, dest='bundle',
            help="Which dependencies to bundle")
        
        add('--bundle-path', default=False, dest='bundle_path',
            help="The folder used for downloaded dependencies")

        add('--bundle-options', dest='bundle_options', default=False,
            action='store_true', help='List dependencies which may be bundled')

        add('--bundle-show', dest='bundle_show', default=False,
            action='store_true', help='Show the dependency bundle options')

        for d in dependencies:
            add('--%s-path' % d, dest= DEP_PATH_DEST % d, default=False,
                help='path to %s' % d)
        
    def is_system_dependency(self, name):
        return is_system_dependency_impl(name)

    def load_dependency(self, name):
        """
        Load a specific dependency in the OptionsContext
        Notice, that it might not have been downloaded yet, in
        that case we mark the options dirty
        """
        path = dependency_config[DEP_PATH_DEST % name]
        
        if path:

            if not os.path.isdir(path):
                global options_dirty
                options_dirty = True
            else:
                                    
                self.recurse(path)

        else:
            self.fatal('Trying to load dependency %s which is not'
                       ' bundled or has a path' % name)

    def parse_args(self, args = None):
        """
        Parse the arguments passed to the command line
        """

        try:
            super(DependencyOptionsContext, self).parse_args(args)

        except:
            if options_dirty:
                Logs.pprint('YELLOW', 'Warning: The options might be incomplete as '
                            'some bundled dependencies have not been '
                            'downloaded yet. Run "./waf configure" to fetch them')
            raise
        

    def bundle_options(self):
        """
        Prints the bundle/dependency options
        """
        #self.msg('Bundle options', 'NONE, ALL, ' + ', '.join(dependencies.keys()))
        print('Bundle options:', 'NONE, ALL, ' + ', '.join(dependencies.keys()))
        sys.exit(0)


    def bundle_show(self):
        """
        Show the current bundle options
        """
        print(dependency_config)
        print('wurftool version:', WURFTOOL_VERSION)
        #self.msg('Dependencies bundled', ', '.join(dependency_config.DEPS))
        #self.msg('Bundle path', bundle_path())
        sys.exit(0)


    def preprocess_dependency_options(self):
        """
        Look in the options for dependencies
        """

        # Remove the two arguments -h and --help to avoid the
        # option parser exiting here. 
        arguments = list(sys.argv)

        if '-h' in arguments: arguments.remove('-h')
        if '--help' in arguments: arguments.remove('--help')
        
        (options, args) = self.parser.parse_args(arguments)
        
        if options.bundle_show:
            self.bundle_show()

        if options.bundle_options:
            self.bundle_options()

        needs_configure = False

        if options.bundle_path:
            path = os.path.abspath(os.path.expanduser(options.bundle_path))
            dependency_config['BUNDLE_PATH'] = path
            needs_configure = True

        if options.bundle:
            dependency_config['BUNDLE'] = self.expand_bundle_argument(options.bundle)
            needs_configure = True

        # Update the path to the bundled dependencies
        if needs_configure:
            for d in dependencies:

                config_key = DEP_PATH_DEST % d

                if d in dependency_config['BUNDLE']:

                    # Build the path
                    bundle_name = d

                    if dependencies[d]['tag']:
                        bundle_name = bundle_name + '-' + dependencies[d]['tag']

                    bundle_path = dependency_config['BUNDLE_PATH']
                    bundle_path = os.path.join(bundle_path, bundle_name)
                    
                    dependency_config[config_key] = bundle_path
                    
                else:
                    dependency_config[config_key] = False

        def check_not_bundled(name, msg):
            if name in dependency_config['BUNDLE']:
                self.fatal('%s -> %s' % (msg, name))

        for d in dependencies:

            path_key = DEP_PATH_DEST % d
            path_value = getattr(options, path_key)

            if path_value:
                check_not_bundled(d, 'Path for already bundled dependency')
                dependency_config[path_key] = os.path.abspath(os.path.expanduser(path_value))
                needs_configure = True

        if needs_configure:
            # Inject the configure command into the arguments
            sys.argv.append('configure')


    def expand_bundle_argument(self, arg):
        """
        Expands the bundle arg so that e.g. 'ALL,-gtest' becomes the
        right set of dependencies
        """
        arg = arg.split(',')
        
        if 'NONE' in arg and 'ALL' in arg:
            self.fatal('Cannot specify both ALL and NONE as dependencies')

        candidate_score = dict([(name, 0) for name in dependencies])

        def check_candidate(c):
            if c not in candidate_score:
                self.fatal('Cannot bundle %s, since it is not specified as a'
                           ' dependency' % c)

        for a in arg:
            
            if a == 'ALL':
                for candidate in candidate_score:
                    candidate_score[candidate] += 1
                continue

            if a == 'NONE':
                continue

            if a.startswith('-'):
                a = a[1:]
                check_candidate(a)
                candidate_score[a] -= 1

            else:
                check_candidate(a)
                candidate_score[a] += 1

        candidates = [name for name in candidate_score if candidate_score[name] > 0] 
        return candidates
            

@conf
def fetch_git_dependency(self, name):

    dep = dependencies[name]

    tag = dep['tag']
    repo_url = dep['repo_url']

    repo_dir = dependency_config[DEP_PATH_DEST % name]

    if not repo_dir:
        self.fatal('Trying to load dependency %s which is not'
                   ' bundled or has a path' % name)

    if os.path.isdir(repo_dir):

        # if we do not have a tag means we are following the
        # master -- ensure we have the newest by doing a pull
        Logs.debug('%s dir already exists skipping git clone' % repo_dir)

        if not tag:
            self.git_pull(repo_dir, quiet = True)

    else:

        self.repository_clone(repo_dir, repo_url)

        if tag:
            self.git_checkout(repo_dir, tag)

    if self.git_has_submodules(repo_dir):
        self.git_submodule_init(repo_dir)
        self.git_submodule_update(repo_dir)


@conf
def load_dependency(self, name):

    if not name in dependencies:
        self.fatal('Error load called for non existing dependency %s' % name)


    if isinstance(self, ConfigurationContext):

        if name in dependency_config['BUNDLE']:
            self.fetch_git_dependency(name)

    recurse_dir = dependency_config[DEP_PATH_DEST % name]

    if not os.path.isdir(recurse_dir):
        self.fatal('Could not find dependency %s at %s, run ./waf configure'
                   % (name, recurse_dir))

    self.recurse(recurse_dir)

@conf
def is_system_dependency(self, name):
    return is_system_dependency_impl(name)


####################
# SkipDependencyDist
####################

class SkipDependencyDist(Scripting.Dist):
    """
    Ensures that the dist command does not include the dep file
    """
    def get_excl(self):
        return super(SkipDependencyDist, self).get_excl() + ' **/'+ DEPENDENCY_FILE



##################
# Add a dependency
##################
def add_dependency(name, repo_url, tag = None):
    """
    Adds a dependency 
    """

    #print("Adding",name)
        
    if name in dependencies:
        dep = dependencies[name]

        # check that the existing dependency specifies
        # the same tag

        if tag !=  dep['tag']:
            raise Errors.WafError('Existing dependency %s tag mismatch %s <=> %s' %
                                  (name, tag, dep['tag']))

        if repo_url != dep['repo_url']:
            raise Errors.WafError('Exising dependency %s repo_url mismatch %s <=> %s' %
                                  (name, repo_url, dep['repo_url']))

    else:

        dependencies[name] = dict()
        dependencies[name]['tag'] = tag
        dependencies[name]['repo_url'] = repo_url


            
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
        if k == DEPENDENCY_FILE:

            # We also clean the dependency config
            # if it is there
            os.remove(DEPENDENCY_FILE)


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
            





