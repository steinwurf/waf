Introduction
============

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle / resolve library dependencies. The goal is to
add functionality to Waf such that it can clone and download needed dependencies
automatically.

License
=======
This project is under the same BSD license as the Waf project. The license text
can be found here: https://github.com/waf-project/waf/blob/master/waf-light#L6-L30

Building our custom Waf binary
==============================

Clone the repository::

    git clone https://github.com/steinwurf/waf.git

Build waf and include our custom tools::

    python waf configure
    python waf build

This will produce a waf binary in the `build` folder which we may copy into our
projects.

Source code
===========

The modifications and additions to Waf are in the `src/wurf` folder. The
main file included by Waf is the `src/wurf/waf_entry_point.py`. This is a great
place to start to understand our additions to `Waf`.

Waf will load this file automatically when starting up, which is acheived using
the `--prelude` option of Waf. Described in the Waf book
[here](https://waf.io/book/#_customization_and_redistribution).

Waf specific code
=================

Code that uses/imports code from core `Waf` are prefixed with `waf_`. This makes
it easy to see which files are pure Python and which provide the integration
points with `Waf`.

Tests
=====

To ensure that the tools work as intended way we provide a set of
tests. To run the tests invoke::

      tox

See tox documentation here: https://tox.readthedocs.org/en/latest/

Specifying a dependency
========================

In the following we will provide an overview of the options (and sub-options)
available when specifying a dependency::

    def resolve(ctx):
        ctx.add_dependency(
            name='foo',
            ...)

recurse (boolean)
-----------------
This option specifies whether waf should recurse into the dependency folder.

This is useful if the dependency is itself a waf probject. When recursing into
a folder waf will look for a wscript in the folder and execute its commands.

Currently we will automatically (if recurse is True), recurse into and execute
following waf commands: (resolve, options, configure, build)

If you have a wscript where you would like to recurse dependencies for a custom
waf commands, say upload. This can be done by using the adding the following
to your wscript's upload function::

    def upload(ctx):
        ... your code
        # Now lets recurse and execute the upload functions in dependencies
        # wscripts.

        import waflib.extras.wurf.waf_resolve_context

        # Call upload in all dependencies
        waf_resolve_context.recurse_dependencies(self)


Options (building new Waf binaries)
===================================

`--skip_network_tests`
---------------------------
To test the freshly built Waf binary some unit test use network connectivity
to resolve dependencies. This makes the tests slow. It would therefore be
beneficial to remove these tests when running e.g. on a build system.

An example of such a test is the `self_build` test. The `self_build` test will
invoke a freshly built `waf` binary with the wscript used to build it -
yes very meta :)

Passing `--skip_network_tests` will skip any unit tests which rely on network
connectivity.

Features of Waf with resolve capabilities
=========================================

`--fast-resolve`
----------------
As default the resolver will be invoked when configuring a waf project i.e.
invoking `python waf configure ...`. Depending on the number of dependencies
this may take some time to complete. This is problematic if an user is for
example re-configuring to change compiler.

Providing the `--fast-resolve` option should only invoke the resolvers for
dependencies that have not already been downloaded. Already downloaded
dependencies should be loaded from the cache.

`--fast-resolve` is also useful when manually specifying resolve method for a
dependency e.g. to manually set the path of a dependency `foo` using
`--fast-resolve` will load all other dependencies from cache::

    python waf configure --foo-path /tmp/foo --fast-resolve

Support for `resolve.json`
--------------------------
Providing third-party tooling to work with the dependencies, i.e. monitoring
the dependencies and sending push notifications when new versions are available
etc. is a lot easier if dependencies are stored outside the `wscript` in an
easy to process data structure.

It is therefore recommended that users specify dependencies using a
`resolve.json` file.

If needed it is still possible to define the `resolve(...)` function
in the `wscript`. This should only be used in situations where some information
about a dependency is not known until runtime or when some computations are
needed to determine some information regarding a dependency. In that case an
user can define the `resolve(...)` function in the `wscript` and write the
needed Python code.

To support both these ways of configuring we define the following "rules":

1. The user defined `resolve(...)` function will always be called before looking
   for a `resolve.json` file.
2. It is valid to mix both methods to define dependencies.

Future features
===============

The following list contains the work-items that we have identified as "cool"
features for the Waf dependency resolve extension.

Build symlinks
--------------
The purpose of this feature is to provide stable locations in the file system
for the downloaded dependencies. This is very similar to how pytest (under
Linux) maintains a symlink to the latest unit-test invocation as
`/tmp/pytest-of-user/pytest-current` (this does seem to only happen when using
`tox`, needs investigation).

As a default several folders will be created during the process of resolving
dependencies. Several projects can share the same folder for resolved
dependencies (this is controlled using the `--bundle-path` option). To avoid
confusing / error-prone situations the folders are considered immutable. This
results in some overhead and knowing paths to dependencies may change as new
versions of them become available. E.g if the `gtest` dependency is currently
located under `/tmp/gtest-1.6.7-someh4sh`, as soon as version `1.6.8` is
released and the user re-runs `python waf configure ...` the path may be
updated to `/tmp/gtest-1.6.8-someh4sh` as the resolver noticed a new version
became available.

This is problematic e.g. for IDE configurations where an user needs to manually
go and update the path in the IDE to the new location.

To avoid this problem we propose to create a `build_symlinks` (controllable
using the `--symlinks-path` option) folder in the root of the project containing
symlinks to the named dependencies.

For the previous example we would see the following in the `build_symlinks`
folder::

    $ ll build_symlinks/
    total 0
    lrwxrwxrwx 1 usr usr 29 Feb 20 20:55 gtest -> /path/to/gtest-1.6.7-someh4sh

After re-running `./waf configure ...`::

    $ ll build_symlinks/
    total 0
    lrwxrwxrwx 1 usr usr 29 Feb 20 20:57 gtest -> /path/to/gtest-1.6.8-someh4sh


Add `--force-resolve` option
----------------------------
Certain resolvers utilize "shortcuts" such as using cached information about
dependencies to speed the resolve step. Providing this option should by-pass
such optimizations and do a full resolve - not relying on any form of cached
data.

Print traceback if `-v` verbose flag is specified
-------------------------------------------------
To make error messages user-friendly the default is to redirect full tracebacks
(showing where an error originated), to the log files. However, if running on
a build system it is convinient to have the full traceback printed to the
terminal, this avoid us having to log into the machine an manually retrieve the
log file.

To support this behaviour will will print the error traceback to the screen
if the verbose flag `-v` is specified.

Dump resolved dependencies information to json.
-----------------------------------------------
To support third party tooling working with information about an already
resolved dependency we implement the `--dump-resolved-dependencies` option.

This will write out information about resolved dependencies such as semver tag
chosen etc.

Add `--freeze` option
---------------------

The freeze option will write `frozen_dependencies.json` to the root folder.
This file will fix the path to the different named dependencies, all
dependencies needed must be found in the fozen file if present.

If the `frozen_dependencies.json` is present it will take precedence over all
resolvers besides the `--project-path` options.

This makes it possible to easily the create standalone archives, by simply
invoking::

    python waf configure --freeze
    python waf dist



Bundle dependencies
===================

The basic

Design
======

Notes
-----

It does not make sense to store anything but the path and sha1 in the
persistant cache files. The reason is that with the sha1 we know that the
options passed to add_dependency(...) is the same as during the active resolve.

Location of the source files is a bit tricky. The reason being that Waf will
move these files to waflib.extras, this is actually a good thing because if we
explicitly import from either waflib.extras or use a relative include such as
from . import. Then we avoid conflicts with system installed packages with the
same name.

Now when running unit tests our source files will be under:

- src/wurf/wurf_xyz.py

Third party dependencies will be under:

- /home/mvp/bundle_dependencies/some_name/thing.py

So


------

The basic idea to extend waf with the capability of fetching/downloading
dependencies of projects automatically::

    class Resolver:

        def options(self, ctx):
            ctx.add_option('')

        def resolve(self, ctx):
            print(ctx.options.foo)


    class Resolver:

        def options(self, ctx):
            ctx.add_option('')

        def resolve(self, ctx):
            print(ctx.options.foo)


Log output / debugging
======================

We use the logging system provided by `waf`. If you have an issue with the
resolve functionality you can add the `-v` verbose flags to see more information
pass `-vvv` to see all debug information. Alternatively you can use the
`--zones` filter to see the resolver debug messages only.

::

    python waf configure -v --zones=resolve




Fixing unit tests
=================

If some of the unit tests fail, it may sometimes be helpful to be able to
go the test folder and e.g. invoke the waf commands manually. We are using
Tox to ensure that our tests run in a specific environment, so if we want
to use the same environment e.g. with a specific version of the Python
interpreter you need to activate it.

Example
-------

Say we run the test and see the following::

  ______________________________ summary _______________________________
  py27: commands succeeded
  ERROR:   py31: commands failed
  ERROR:   py34: commands failed

Seems we have a problem related to Python 3.x support. The names `py31` and
`py34` refers to the environment where the failed tests ran. Lets say we
want to try to manually run the failing commands in the
`py31`environment. Tox uses virtualenv and stores these in `.tox` in the
project root folder, to activate it we run::

  $ source .tox/py31/bin/activate

You should now use the right version of the Python interpreter and have
access to all the test dependencies (if any). So you can navigate to the
directory where the tests failed and play around. Typically you can use the
pytest symlink::

    /tmp/pytest-of-user/pytest-current/some_folder_containing_failed_test

Once you are done exit the virtualenv by running::

  $ deactivate

Note, the above does not work anymore since we now invoke Tox from within waf
and pass needed paths to it.

Finding the log output etc.
---------------------------

We use pytest to run the waf commands (integration tests). pytest will create
temporary folders etc. when running the tests. These are created on the fly and
numbered.

One great feature of pytest is that is will maintain a symbolic link to the most
current test invocation. On Linux this is found under::

    /tmp/pytest-of-user/pytest-current/

Where the `user` will be replace with the your user's name.
