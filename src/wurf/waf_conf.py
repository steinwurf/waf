#! /usr/bin/env python
# encoding: utf-8

# This file contains the methods added to the ConfigurationContext
# and BuildContext objects. This means that you can use these methods
# inside the configure(...) and build(...) functions defined in most
# wscripts.

import sys
import os

from waflib.Configure import conf
from waflib.Errors import WafError
from waflib import Logs
from waflib import Context
from waflib import Scripting

from . import waf_resolve_context
from . import virtualenv
from . import rewrite
from . import pip_tools
from . import error
from .registry import Registry


def extend_context(f):
    """
    Decorator: attach new  functions to waflib.Context. It is like
    Waf's conf decorator. But instead of just extending the
    ConfigurationContext and BuildContext this will extend the
    base Context.

    :param f: Method to bind
    """
    setattr(Context.Context, f.__name__, f)
    return f


@conf
def dependency_path(ctx, name):
    """
    Returns the dependency path as a string
    """
    return waf_resolve_context.dependency_cache[name]["path"]


@conf
def dependency_node(ctx, name):
    """
    Returns the dependency path as a Waf Node
    """
    # find_node(..) requires a str
    return ctx.root.find_node(str(ctx.dependency_path(name)))


@conf
def has_dependency_path(ctx, name):
    """
    Returns true if a path is available for the dependency
    """
    return name in waf_resolve_context.dependency_cache


@conf
def is_toplevel(self):
    """
    Returns true if the current script is the top-level wscript
    """
    return self.srcnode == self.path


@conf
def recurse_dependencies(ctx):
    """Recurse the dependencies which have the resolve property set to True.

    :param ctx: A Waf Context instance.
    """

    # See if we have a log file, we do this here to avoid raising
    # excpetions and destroying traceback inside the excpetion
    # handler below.
    try:
        logfile = ctx.logger.handlers[0].baseFilename
    except Exception:
        logfile = None

    # Since dependency_cache is an OrderedDict, the dependencies will be
    # enumerated in the same order as they were defined in the wscripts
    # (waf-tools should be the first if it is defined)
    for name, dependency in waf_resolve_context.dependency_cache.items():
        if not dependency["recurse"]:
            Logs.debug(f"resolve: Skipped recurse {name} cmd={ctx.cmd}")

            continue

        path = dependency["path"]

        Logs.debug(f"resolve: recurse {name} cmd={ctx.cmd}, path={path}")

        try:
            # @todo mandatory is False here, which means that no wscript
            # is required to exist. Not sure if this is really a good idea?
            # As a minimum it should be described here why that is the
            # case. Because it opens the door to errors where e.g. the
            # user points the dependency to some empty folder. Which will
            # not fail them - but probably should?
            # There is a unit test in:
            # test/fail_recurse/test_fail_recurse.py which should fail
            # if mandatory is changed to True
            #
            # str() is needed as waf does not handle unicode in find_node
            ctx.recurse([str(path)], once=False, mandatory=False)
        except WafError as e:
            msg = f'Recurse "{name}" for "{ctx.cmd}" failed with: {e.msg}'

            if logfile:
                msg = f"{msg}\n(complete log in {logfile})"
            else:
                msg = f"{msg}\n(run with -v for more information)"

            raise WafError(msg=msg, ex=e)


@extend_context
def create_virtualenv(
    ctx, cwd=None, env=None, name=None, overwrite=True, system_site_packages=False
):
    return virtualenv.VirtualEnv.create(
        ctx=ctx,
        log=Logs,
        cwd=cwd,
        env=env,
        name=name,
        overwrite=overwrite,
        system_site_packages=system_site_packages,
    )


@extend_context
def pip_compile(ctx, requirements_in, requirements_txt):
    pip_tools.compile(ctx, requirements_in, requirements_txt)


@extend_context
def ensure_build(ctx):
    """
    Ensure that we've run the build step before running the current command.
    """

    if "build" not in sys.argv:
        Scripting.run_command("build")


@extend_context
def rewrite_file(ctx, filename):
    return rewrite.rewrite_file(filename=filename)


@extend_context
def project_version(ctx):
    """
    Return the project version. If the project is not a git repository
    None is returned. If the project is a git repository the version
    is constructed as follows:

    1. If the current commit matches a tag the tag is used as the version.
    2. If the current commit does not match a tag the latest tag and
       current commit is used as the version.
    3. If the repository contains uncommitted changes "-dirty" is appended.

    Examples:

        gc0b0b0b
        gc0b0b0b-dirty
        1.0.0
        1.0.0-dirty
        1.0.0-gc0b0b0b
        1.0.0-gc0b0b0b-dirty # all together now

    :param ctx: A Waf Context instance.
    """

    # To avoid logs going to stdout create an logger
    bldnode = ctx.path.make_node("build")
    bldnode.mkdir()

    log_path = os.path.join(bldnode.abspath(), "version.log")

    old_logger = ctx.logger
    ctx.logger = Logs.make_logger(path=log_path, name="version")
    ctx.logger.debug("wurf: project version execute")

    registry = Registry()
    registry.provide_value("ctx", ctx)
    registry.provide_value("git_binary", "git")
    git = registry.require("git")

    try:
        # Build the registry
        cwd = ctx.path.abspath()
        if not git.is_git_repository(cwd):
            return None

        commit = git.current_commit(cwd)
        tag = ([None] + git.tags(cwd))[-1]
        if tag is not None:
            tag = tag.rstrip()
            tag_commit = git.checkout_to_commit_id(cwd, tag)
            if tag_commit == commit:
                commit = None
        dirty = git.is_dirty(cwd)

        # Build the version slug
        version = []
        if tag is not None:
            version.append(tag)
        if commit is not None:
            version.append(commit[:7])
        if dirty:
            version.append("dirty")
        version = "-".join(version)

        return version
    except error.CmdAndLogError as e:
        ctx.logger.debug(f"wurf: project version failed: {e}")
        return None
    finally:
        ctx.logger = old_logger
