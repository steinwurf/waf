#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from waflib import Utils
from waflib import Context
from waflib import Options
from waflib import Logs

from waflib.Errors import WafError

from . import registry
from .error import CmdAndLogError
from .error import WurfError
from .dependency_manager import DependencyManager

from waflib.extras import semver
from waflib.extras import archive


# To create the tree. https://gist.github.com/hrldcpr/2012250

dependency_cache = {}
"""Dictionary that stores the dependencies resolved.

The dictionary will be initialized by the WafResolveContext and can be
used by all other contexts or tools that need to access the
dependencies. The idea is that this will be the single place to look to
figure out which dependencies exist.
"""


class WafResolveContext(Context.Context):
    """resolves the dependencies specified in the wscript's resolve function"""

    cmd = "resolve"
    fun = "resolve"

    def __init__(self, resolve=False, skip_internal=False, **kw):
        """Create a WafResolveContext"""
        super(WafResolveContext, self).__init__(**kw)

        # We only want to carry out the actual resolve once, when intially
        # created by the options context. However, this context may
        # be create multiple times e.g. if the user passes resolve as a
        # command to run a resolve without a configure - this is ok. But,
        # in that case we don't want to run resolve twice.
        self.resolve = resolve
        self.skip_internal = skip_internal

    def execute(self):
        if not self.resolve:
            # Skip out if we are should not execute - see __init__ for
            # explanation
            return

        # Check whether the main wscript has a resolve function defined,
        # if not we create one. This is also done for other functions such
        # as options by waf itself. See:
        # https://gitlab.com/ita1024/waf/-/blob/89175bf97/waflib/Scripting.py#L203-209
        if "resolve" not in Context.g_module.__dict__:
            Context.g_module.resolve = Utils.nada

        # Create the nodes that will be used during the resolve step. The build
        # directory is also used by the waf BuildContext
        self.srcnode = self.path
        self.bldnode = self.path.make_node("build")
        self.bldnode.mkdir()

        default_resolve_path = os.path.join(
            self.path.abspath(), "resolved_dependencies"
        )

        default_symlinks_path = os.path.join(self.path.abspath(), "resolve_symlinks")

        self.registry = registry.resolve_registry(
            ctx=self,
            git_binary="git",
            semver=semver,
            archive_extractor=archive.extract,
            default_resolve_path=default_resolve_path,
            resolve_config_path=self.resolve_config_path(),
            default_symlinks_path=default_symlinks_path,
            waf_utils=Utils,
            args=sys.argv[1:],
            project_path=self.path.abspath(),
            waf_lock_file=Options.lockfile,
            skip_internal=self.skip_internal,
        )

        # Enable/disable colors based on the currently used terminal.
        # Note: this prevents jumbled output if waf is invoked from an IDE
        # that does not render colors in its output window
        Logs.enable_colors(1)

        # Lets make a different log file for the different resolver chains
        configuration = self.registry.require("configuration")

        path = os.path.join(
            self.bldnode.abspath(), configuration.resolver_chain() + ".resolve.log"
        )

        self.logger = Logs.make_logger(path, "resolve")
        self.logger.debug(f"wurf: Resolve execute {configuration.resolver_chain()}")

        self.dependency_manager: DependencyManager = self.registry.require(
            "dependency_manager"
        )

        try:
            # Calling the context execute will call the resolve(...) functions
            # in the wscripts.
            super(WafResolveContext, self).execute()

        except WurfError as e:
            self.logger.debug("Error in resolve:\n", exc_info=True)
            self.fatal(str(e))
        except Exception:
            raise

        # Get the cache with the resolved dependencies
        global dependency_cache
        dependency_cache = self.registry.require("dependency_cache")

        self.logger.debug(f"wurf: dependency_cache {dependency_cache}")

        # If needed execute any actions which cannot run until after the
        # dependency resolution has completed
        post_resolver_actions = self.registry.require("post_resolver_actions")

        for action in post_resolver_actions:
            action()

    def post_recurse(self, node):
        # As the last step in recurse, try to load the dependencies from the
        # 'resolve.json' file if it is present next to the wscript.
        # This is done after calling a possible user-defined
        # resolve() function, since we always want to allow the user to
        # run custom code before the actual resolving starts.

        try:
            self.dependency_manager.load_dependencies(
                self.path.abspath(), mandatory=False
            )
        except ValueError as e:
            # The ValueError is raised when the json is malformed. We
            # could potentially catch more errors here. But, we can
            # expand this if needed to catch more error types later..
            msg = (
                f"Error in load dependencies (resolve.json) {self.path.abspath()}: {e}"
            )
            self.logger.debug(msg, exc_info=True)
            self.fatal(msg)

        super(WafResolveContext, self).post_recurse(node)

    def is_toplevel(self):
        """
        Returns true if the current script is the top-level wscript
        """
        return self.srcnode == self.path

    def resolve_config_path(self):
        """Returns the bundle config path.

        The bundle config path will be used to store/load configuration for
        the different dependencies that are resolved.
        """
        return self.bldnode.abspath()

    def cmd_and_log(self, cmd, **kwargs):
        # Seems the new waf needs the cwd to be a Node object. We do this
        # adaption here to avoid introducing additional Waf dependencies in the
        # other parts of the code.
        if "cwd" in kwargs:
            cwd = kwargs["cwd"]
            kwargs["cwd"] = self.root.find_dir(str(cwd))
            assert kwargs["cwd"]

        try:
            return super(WafResolveContext, self).cmd_and_log(cmd=cmd, **kwargs)
        except WafError as e:
            # @todo Do we need to include the traceback to the original
            # exception here? See: http://bit.ly/2njVD5V
            raise CmdAndLogError(error=e)
        except Exception:
            raise
