#! /usr/bin/env python
# encoding: utf-8

import sys

# This file is the "entry point" for all our extensions to Waf. The main
# purpose is to import the custom contexts used. When a context is
# imported it auto registers with Waf and overrides any contexts that were
# previously defined for a specific command.

from waflib import Errors

# A general note on the Context. Waf uses a meta-classes registration
# system for the Context classes. This means that to register e.g. a new
# ConfigurationContext it is enough to simply import the module where the
# context class is defined. When the Python interpreter sees the definition
# waf will auto-register that this should be the new
# ConfigurationContext. Below we will import a number of modules containing
# our custom contexts.
#
# The options context is instantiated automatically every time waf is
# invoked.
#
# It will recurse out in the options(...) functions defined in the
# wscript. We have customized it to launch the waf_resolve_context which
# first recurses the resolve(...) functions to fetch any defined
# dependencies.
from . import waf_resolve_context
from . import waf_options_context
from . import waf_configuration_context
from . import waf_build_context
from . import waf_install_context
from . import waf_standalone_context

# We add a number of methods to the ConfigurationContext and BuildContext
# objects used in Waf's configure(...) and build(...) functions (found in
# most wscripts). To register these functions we just need to import the module
# where they are defined:
from . import waf_conf

# Silence pyflakes on unused imports
# https://mail.python.org/pipermail/python-list/2013-May/646440.html
assert waf_resolve_context
assert waf_options_context
assert waf_configuration_context
assert waf_build_context
assert waf_install_context
assert waf_standalone_context
assert waf_conf


def _check_minimum_python_version(major, minor):
    """
    Check that the Python interpreter is compatible.
    @todo write why we have this requirement
    """
    if sys.version_info[:2] < (major, minor):
        raise Errors.ConfigurationError(
            "Python version not supported: {0}, "
            "required minimum version: {1}.{2}".format(
                sys.version_info[:3], major, minor
            )
        )


# waf_entry_point is loaded first in every project,
# therefore it is a good entry point to check the minimum Python version
_check_minimum_python_version(3, 6)
