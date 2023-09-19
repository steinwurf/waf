News for Waf
============

This file lists the major changes between versions. For a more detailed list
of every change, see the Git log.

Latest
------
* Major: Removed tag database and by extension the ``ExistingTagResolver``.
* Major: Use lock files (if present) in dependencies when resolving.
* Major: Removed the ``override`` attribute.
* Major: Changed the ``optional`` attribute to mean that the dependency can
  be enabled or disabled by the user. This is useful for dependencies that
  are only required for certain features or on certain platforms.
* Patch: Fixed bug in UrlDownload where some file downloads would result in
  a 403 error due to the user-agent not being set.
* Major: Removed ``add_dependency`` from the context, as all dependencies
  must now be added in the ``resolve.json`` file.
* Patch: Fixed issue where 'resolve' was not utilizing the lock paths or
  versions file.
* Major: Removed support for multiple sources for the same dependency.
  The support for sources is still there, but only the first source will be
  used.
* Major: Removed fast-resolve option as this behavior should now be covered
  by the use of lock files.
* Minor: Allow locking the paths using the locked versions.
* Major: Split ``lock_resolve.json`` into two separate lock files, one for
  versions and one for paths.
* Patch: Fixed bug that caused the lock_resolve.json to not be used correctly.
* Patch: Fixed bug that caused ``--lock_versions`` to fail when using in
  combination with ``ExistingTagResolver``.
* Minor: Add better error messages for mismatched dependencies.
* Minor: Recursively pull submodules
* Minor: Adding ensure_build function to Waf's Context object.
* Minor: Added a pip_compile helper function on Waf's Context object.
* Minor: Added support for .wurf_config. This allows changing the default
  resolve path.
* Minor: Do not rewrite git protocol if fully specified
* Minor: Fix Windows support
* Patch: Fix bug when using virtualenv for virtual environments.
* Patch: Move the rewrite_file helper to all contexts (before it was only
  available in the build context).
* Patch: Added the '--force' flag to the git checkout command.

6.0.0
-----
* Minor: Change location of tag registry.
* Major: Rename Error to WurfError to make it's origin more obvious.
* Minor: Added --skip_internal option which allows the user to skip internal
  dependencies when resolving.
* Major: Updated to waf 2.0.22
* Major: Make resolve symlinks relative.
* Minor: Added support for git_protocol `ssh://git@`
  (used when "cloning" with pip).
* Minor: Added support for custom git_protocols.
* Patch: Recurse dependencies of dependencies before the dependency.
* Major: Change the default interpreter to python3
* Patch: Fix resolve such that it won't run twice when invoked explicitly.
* Minor: Allow resolve without configuration, by calling python waf resolve.
* Minor: Added registry for the OptionsContext - this allows us to build git
  helpers etc.
* Minor: Adding helper functionality for rewriting files. This is useful
  when releasing projects and some files need to be updated programmatically.
* Minor: Added git checkout resolver which will reuse previously checked out
  checkouts, and thereby making the configure step faster.
* Patch: Fix dependency_node(..) function to work with unicode strings.
* Major: Upgraded to virtualenv 16.4.3. The option --no-site-packages was
  deprecated and replaced with --system-site-packages. Which is now reflected
  in the API to create virtualenvs.
* Major: Removed pip_local_download, pip_local_install, pip_install from the
  virtualenv implementation. Users might as well directly call run with the
  appropriate command.
* Major: Prevent creation of virtualenv in build folder
* Patch: Make the virtualenv clone shallow.
* Major: Remove the explicit dependency on virtualenv. Instead we will
  automatically download the virtualenv dependency.
* Minor: Updated waf to 2.0.10.
* Patch: Hide the output of the mklink command on Windows when calling the
  create_symlink function (the output is logged when an error occurs)
* Minor: Allow persistent virtualenv
* Minor: Added capability to prevent git dependencies from pulling submodules.
* Minor: Added Context dependency_node() function to return a waf node to a
  dependency. Making it easy to use Waf's ant_glob(...) function.
* Major: Updated the create_virtualenv(...) function for virtual environments.
* Minor: Added the clang_compilation_database tool.
* Minor: Add symlink in source folder to the current build folder. The symlink
  called 'build_current' will point to Waf's build folder.
* Patch: Move recurse_dependencies() to Waf's execute_build() function. Since
  this is known to only be called once. This eliminates using the is_toplevel to
  avoid infinite recursion.
* Patch: Refactor symlink code into a standalone utility. This makes it
  reusable by other tools which need to make symlinks.
* Patch: Update to newest pytest-testdirectory plugin
* Minor: Adding override attribute.
* Minor: Added post_resolve.
* Minor: Use a version of python-archive which preserves file permissions.
* Minor: Added exceptions for accidental empty options.
* Major: Full rewrite of our Waf dependency resolve code.
* Minor: Support for new resolver options.
* Minor: Adding support for resolve.json files.
* Minor: Updated waf to 1.9.8.
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
