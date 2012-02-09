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

#################################
# Load the wurftools dependencies
#################################

def options(opt):
    opt.load('toolchain_cxx')
    opt.load('git')

def configure(conf):
    conf.load('toolchain_cxx')
    conf.load('git')


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
        if k == '.dep_store':

            # We also clean the dependency config
            # if it is there
            os.remove('.dep_store')


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

DEP_FILE = '.dep_store'
""" The config file which tracks which dependencies have been choosen """

RECURSE_DEPENDENCY = 0
""" The dependency wscript should be recursed """

CHECK_DEPENDENCY = 1
""" The dependency should be checked only """

OPTIONS_NAME = 'Dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """ 




def do_bundle_dependency(name):
    """
    Returns whether the dependency is bundled
    """
    return name in dependency_config.DEPS


def bundle_path():
    """
    Returns the path to the bundle path
    """
    path = dependency_config.BUNDLE_PATH

    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    return path


def dependency_path(name, tag = None):
    """
    Returns the bundle directory
    """

    folder = name
    
    if tag:
        folder = folder + '-' + tag
    
    path = bundle_path()
    return os.path.join(path, folder)




class DependencyOptionsContext(OptionsContext):

    def __init__(self, **kw):
        """
        Constructor for the dependency options
        """
        
        super(DependencyOptionsContext, self).__init__(**kw)

        self.add_basic_options()
        self.load_config()

        if '--bundle' in ''.join(sys.argv):
            self.bundle_args()
        else:
            self.save_and_exit = False
        
    def load_config(self):
        """
        Loads dependencies from the config file
        """
        
        try:
            dependency_config.load(DEP_FILE)
        except Exception:
            pass

        if not dependency_config.DEPS:
            dependency_config.DEPS = ['NONE']

        if not dependency_config.BUNDLE_PATH:
            dependency_config.BUNDLE_PATH = DEFAULT_BUNDLE_PATH


    def add_basic_options(self):
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


        self.expand_args()
        self.check_args()

        if self.save_and_exit:
            dependency_config.store(DEP_FILE)
            sys.exit(0)


        if Opt.options.bundle_show:
            self.bundle_show()

        if Opt.options.bundle_options:
            self.bundle_options()
            

    def bundle_options(self):
        """
        Prints the bundle/dependency options
        """
        #self.msg('Bundle options', 'NONE, ALL, ' + ', '.join(dependencies.keys()))
        print 'Bundle options: ' + 'NONE, ALL, ' + ', '.join(dependencies.keys())
        sys.exit(0)


    def bundle_show(self):
        """
        Show the current bundle options
        """
        print 'Dependencies bundled: ' + ', '.join(dependency_config.DEPS)
        print 'Bundle path ' + bundle_path()
        #self.msg('Dependencies bundled', ', '.join(dependency_config.DEPS))
        #self.msg('Bundle path', bundle_path())
        sys.exit(0)

    def bundle_args(self):
        """
        Parses the --bundle argument done before any other
        arguments are parsed by the options context. This
        is done so that we know in advance what to do when
        the add_dependency function is called.
        """

        self.save_and_exit = False
        (o,l) = self.parser.parse_args()

        if o.bundle:
            bundle_args = o.bundle.split(',')

            if dependency_config.DEPS != bundle_args:            
                dependency_config.DEPS = bundle_args
                self.save_and_exit = True

        if o.bundle_path:
            dependency_config.BUNDLE_PATH = o.bundle_path
            self.save_and_exit = True

        
            
    def check_args(self):
        """
        Checks whether the arguments passed to the bundle
        command are valid depedencies
        """
        deps = dependency_config.DEPS

        if 'ALL' in deps:
            self.fatal('Internal error ALL should have been expanded!')
        
        for d in deps:

            if d == 'NONE':
                continue
            
            if d not in dependencies:
                self.fatal('Error "%s" is not a valid / declared dependency' % d)

        if not dependency_config.BUNDLE_PATH:
            self.fatal('Error "%s" bundle path not valid' % dependency_config.BUNDLE_PATH)



    def expand_args(self):
        """
        Expands the bundle args so that ALL,-gtest becomes the
        right set of dependencies
        """
        deps = dependency_config.DEPS

        if 'NONE' in deps and 'ALL' in deps:
            self.fatal('Cannot specify both ALL and NONE as dependencies')

        candidates = []

        for d in deps:

            if d == 'ALL':
                candidates += dependencies.keys()
                continue

            if d.startswith('-'):
                dep = d[1:]

                try:
                    candidates.remove(dep)
                except ValueError:
                    self.fatal('Cannot remove %s when not added to bundel set %r'
                               % (dep, deps))
            else:

                if d in candidates:
                    self.fatal('Depedency %s added more than once' % d)
                else:
                    candidates.append(d)

        dependency_config.DEPS = candidates

    def resolve_status(self, name):
        """
        Figures out the status of a dependency
        """
        status = CHECK_DEPENDENCY
        
        for d in dependency_config.DEPS:
            if d == 'ALL' or d == name:
                status = RECURSE_DEPENDENCY

            if d.startswith('-') and d[1:] == name:
                status = CHECK_DEPENDENCY

        return status

    def bundle_dependency(self, name):
        """
        Returns whether the dependency is bundled
        """
        return do_bundle_dependency(name)

    def add_dependency(self, name, repo_url, tag = None):
        """
        Adds a dependency 
        """
        
        if name in dependencies:
            dep = dependencies[name]

            # check that the existing dependency specifies
            # the same tag

            if tag !=  dep['tag']:
                self.fatal('existing dependency %s tag mismatch %s <=> %s' %
                           (name, tag, dep['tag']))

            if repo_url != dep['repo_url']:
                self.fatal('exising dependency %s repo_url mismatch %s <=> %s' %
                           (name, repo_url, dep['repo_url']))

        else:

            dependencies[name] = dict()
            dep = dependencies[name]

            dep['tag'] = tag
            dep['repo_url'] = repo_url
            dep['status'] = self.resolve_status(name)
            dep['repo_dir'] = dependency_path(name)

    def recurse_dependency(self, name):
        """
        Recurses a specific dependency
        """

        if not name in dependencies:
            raise Errors.WafError('Error recurse called for non existing dependency %s' % name)
    
        dep = dependencies[name]
    
        assert dep['status'] == RECURSE_DEPENDENCY
    
        repo_dir = dep['repo_dir']
    
        if not os.path.isdir(repo_dir):
            global options_dirty
            options_dirty = True
        else:
            self.recurse(repo_dir)

@conf
def list_bundle(self):
    return ','.join(dependency_config.DEPS)

@conf
def bundle_dependency(self, name):
    return do_bundle_dependency(name)

@conf
def recurse_dependency(self, name):

    if not name in dependencies:
        raise Errors.WafError('Error recurse called for non existing dependency %s' % name)

    dep = dependencies[name]

    tag = dep['tag']
    repo_url = dep['repo_url']
    repo_dir = dep['repo_dir']
        
    self.repository_clone(repo_dir, repo_url)

    recurse_dir = ''

    if tag:
        local_clone = dependency_path(name, tag)
    
        self.local_clone_tag(repo_dir, local_clone, tag)
        recurse_dir = local_clone
    else:
        recurse_dir = repo_dir


    if self.git_has_submodules(recurse_dir):
        self.git_submodule_init(recurse_dir)
        self.git_submodule_update(recurse_dir)

    self.recurse(recurse_dir)

####################
# SkipDependencyDist
####################

class SkipDependencyDist(Scripting.Dist):
    """
    Ensures that the dist command does not include the dep file
    """
    def get_excl(self):
        return super(SkipDependencyDist, self).get_excl() + ' **/'+ DEP_FILE








            
            





