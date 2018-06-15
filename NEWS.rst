News for Waf
============

This file lists the major changes between versions. For a more detailed list
of every change, see the Git log.

Latest
------
* Minor: Allow persistant virtualenv
* Minor: Added capability to prevent git dependencies from pulling submodules.
* Minor: Added Context dependency_node() function to return a waf node to a
  dependency. Making it easy to use Waf's ant_glob(...) function.
* Major: Updated the create_virtualenv(...) function for virtual environments.
* Minor: Added the `clang_compilation_database` tool.
* Minor: Add symlink in source folder to the current build folder. The symlink
  called 'build_current' will point to Waf's build folder.
* Patch: Move recurse_dependencies() to Waf's execute_build() function. Since
  this is known to only be called once. This eliminates using the is_toplevel to
  avoid infinite recursion.
* Patch: Refactor symlink code into a standalone utility. This makes it
  reusable by other tools which needs to make symlinks.
* Patch: Update to newest pytest-testdirectory plugin
* Minor: Adding override attribute.
* Minor: Added post_resolve.
* Minor: Use a version of python-archive which perseveres file permissions.
* Minor: Added exceptions for accidental empty options.
* Major: Full rewrite of our Waf dependency resolve code.
* Minor: Support for new resolver options.
* Minor: Adding support for `resolve.json` files.
* Minor: Updated waf to 1.9.8.

Un-released changes
-------------------
* Minor: Allow arbitrary git providers in wurf_dependency_resolve.
* Minor: Allow optional dependencies that might not be resolved if they are
  unavailable to the user.
* Minor: Allow option arguments without the = sign for the options that are
  defined and used in the resolve step (--%s-path and --%s-use-checkout).
* Patch: Reversed dependency build order.

5.0.0
-----
* Major: Added wurf_options to allow the definition of options in dependencies.
* Major: Dependencies are resolved recursively in the ``resolve`` step.
* Major: wurf_tools was replaced by wurf_common_tools that loads the commonly
  used tools automatically.
* Minor: Updated waf to 1.8.14.
* Minor: Updated waf to 1.8.8.
* Patch: Moved Waf submodule from Google Code to Github. Run
  ``git submodule sync`` to update your existing repository.

4.1.0
-----
* Patch: Do not pull the dependency right after cloning it.
* Minor: Changed behavior of dependency resolver when choosing git protocol.
  Git protocol of parent project is used if supported, but falls back on
  ``https://`` if the protocol is unsupported. Protocol can still be
  specified through command line option.
* Minor: Added "ALL" as the default value for the bundle option.

4.0.1
-----
* Patch: Fixed unnecessary need for specifying explicit dependency paths

4.0.0
-----
* Minor: Updated waf to 1.7.12
* Major: Enabled custom git checkout of dependencies

3.0.0
-----
* Major: Restructuring the waf tools
* Major: Moving tool functionality to the external-waf-tools repository

2.0.0
-----
* Minor: Added mkspecs
* Patch: Fixed Python3.x support, broken include statement
* Minor: Added wurf_waf_unit_test tool
* Minor: Added wurf_protoc & wurf_proto_cxx tools for protobuf support

1.0.0
-----
* Minor: Added new tool for following git dependencies. Supports dependency
  resolving based on Semantic Versioning (semver.org)
* Patch: Added simple tests of the build tools
