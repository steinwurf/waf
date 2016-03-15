#! /usr/bin/env python
# encoding: utf-8

import sys

# This file is the "entry point" for all our extensions to Waf. The main
# purpose is to import the custom contexts used. When a context is
# imported it auto registers with Waf and overrides any contexts that were
# previously defined for a specific command.

from waflib import Errors

def _check_minimum_python_version(major, minor):
    """
    Check that the Python interpreter is compatible.
    @todo write why we have this requirement
    """
    if sys.version_info[:2] < (major, minor):
        raise Errors.ConfigurationError(
            "Python version not supported: {0}, "
            "required minimum version: {1}.{2}"
            .format(sys.version_info[:3], major, minor))

# wurf_common_tools is loaded first in every project,
# therefore it is a good entry point to check the minimum Python version
_check_minimum_python_version(2, 7)

# The options context runs automatically every time waf is invoked.
#
# It will recurse out in the options(...) functions defined in the
# wscript. We have customized it to launch the wurf_resolve_context which
# first recurses the resolve(...) functions to fetch any defined
# dependencies.
import waflib.extras.wurf_options_context
import waflib.extras.wurf_resolve_context
