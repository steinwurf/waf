#! /usr/bin/env python
# encoding: utf-8

"""
Waf tool used to track dependencies. Using git tags to track whether a
compatible newer version of a specific library is available. The git
tags must be named after the Semantic Versioning scheme defined here:
www.semver.org

The wscript will look like this:

def options(opt):
    opt.load('wurf_dependency_bundle')

def configure(conf):
    conf.load('wurf_dependency_bundle')

"""

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

OPTIONS_NAME = 'dependency options'
""" Name of the options group """

DEFAULT_BUNDLE_PATH = 'bundle_dependencies'
""" Default folder to use for bundled dependencies """

DEPENDENCY_PATH_KEY = '%s_DEPENDENCY_PATH'
""" Destination of the dependency paths in the options """

DEPENDENCY_CHECKOUT_KEY = '%s_DEPENDENCY_CHECKOUT'
""" Destination of the dependency checkouts in the options """

dependencies = dict()
""" Dictionary storing the dependency information """

def add_dependency(opt, resolver):
    """
    Adds a dependency.
    :param resolver: a resolver object which is responsible for downloading
                     the dependency if necessary
    """
    name = resolver.name

    if name in dependencies:

        if type(resolver) != type(dependencies[name]) or \
           dependencies[name] != resolver:
            raise Errors.WafError('Incompatible dependency added %r <=> %r '
                                  % (resolver, dependencies[name])) 
    else:
        dependencies[name] = resolver

        #bundle_opts = opt.add_option_group(OPTIONS_NAME)
        #bundle_opts.add_option('--%s-path' % name,
        #                       dest = DEPENDENCY_PATH_KEY % name,
        #                       default=False,
        #                       help='path to %s' % name)

def expand_path(path):
    """
    Simple helper to expand paths
    :param path: a directory path to be expanded
    :return: the expanded path
    """
    return os.path.abspath(os.path.expanduser(path))


def options(opt):
    """
    Adds the options needed to control dependencies to the
    options context. Options are shown when ./waf -h is invoked
    :param opt: the Waf OptionsContext
    """
    opt.load('wurf_dependency_resolve')

    bundle_opts = opt.add_option_group(OPTIONS_NAME)

    add = bundle_opts.add_option

    add('--bundle', default=False, dest='bundle',
        help="Which dependencies to bundle")

    add('--bundle-path', default=DEFAULT_BUNDLE_PATH, dest='bundle_path',
        help="The folder used for downloaded dependencies")

    for dependency in dependencies:
        add('--%s-path' % dependency,
            dest=DEPENDENCY_PATH_KEY % dependency,
            default=False,
            help='path to %s' % dependency)

        add('--%s-use-checkout' % dependency,
            dest=DEPENDENCY_CHECKOUT_KEY % dependency,
            default=False,
            help='The checkout to use for %s' % dependency)

def configure(conf):
    """
    The configure function for the bundle dependency tool
    :param conf: the configuration context
    """
    conf.load('wurf_dependency_resolve')

    # Get the path where the bundled dependencies should be
    # placed
    bundle_path = expand_path(conf.options.bundle_path)

    # List all the dependencies to be bundled
    bundle_list = expand_bundle(conf, conf.options.bundle)

    # List all the dependencies with an explicit path
    explicit_list = explicit_dependencies(conf.options)

    # Make sure that no dependencies were both explicitly specified
    # and specifiede as bundled
    overlap = set(bundle_list).intersection(set(explicit_list))

    if len(overlap) > 0:
        conf.fatal("Overlapping dependencies %r" % overlap)

    conf.env['BUNDLE_DEPENDENCIES'] = dict()

    # Loop over all dependencies and fetch the ones
    # specified in the bundle_list
    for name in bundle_list:

        Utils.check_dir(bundle_path)

        conf.start_msg('Resolve dependency %s' % name)

        key = DEPENDENCY_CHECKOUT_KEY % name
        dependency_checkout = getattr(conf.options, key, None)

        dependency_path = dependencies[name].resolve(
            ctx = conf,
            path = bundle_path,
            use_checkout = dependency_checkout)

        conf.end_msg(dependency_path)

        conf.env['BUNDLE_DEPENDENCIES'][name] = dependency_path

    for name in explicit_list:
        key = DEPENDENCY_PATH_KEY % name
        dependency_path = getattr(conf.options, key)
        dependency_path = expand_path(dependency_path)

        conf.start_msg('User resolve dependency %s' % name)
        conf.env['BUNDLE_DEPENDENCIES'][name] = dependency_path
        conf.end_msg(dependency_path)



def expand_bundle(conf, arg):
    """
    Expands the bundle arg so that e.g. 'ALL,-gtest' becomes the
    right set of dependencies
    :param arg: list of bundle dependencies arguments
    """
    if not arg:
        return []

    arg = arg.split(',')

    if 'NONE' in arg and 'ALL' in arg:
        conf.fatal('Cannot specify both ALL and NONE as dependencies')

    candidate_score = dict([(name, 0) for name in dependencies])

    def check_candidate(c):
        if c not in candidate_score:
            conf.fatal('Cannot bundle %s, since it is not specified as a'
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


def explicit_dependencies(options):
    """
    Extracts the names of the dependencies where an explicit
    path have been that have been specified
    :param options: the OptParser object where Waf stores the build options
    """
    explicit_list = []

    for name in dependencies:

        key = DEPENDENCY_PATH_KEY % name
        path = getattr(options, key)

        if path: explicit_list.append(name)

    return explicit_list


@conf
def has_dependency_path(self, name):
    """
    Returns true if the dependency has been specified
    """

    if name in self.env['BUNDLE_DEPENDENCIES']:
        return True

    return False


@conf
def dependency_path(self, name):
    """
    Returns the dependency path
    """
    return self.env['BUNDLE_DEPENDENCIES'][name]


@conf
def is_toplevel(self):
    """
    :return: true if the current script is the top-level wscript otherwise false
    """
    return self.srcnode == self.path








