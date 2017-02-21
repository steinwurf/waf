Introduction
============

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle library dependencies and toolchains.

License
=======
This project is under the same BSD license as the Waf project. The license text
can be found here: https://github.com/waf-project/waf/blob/master/waf-light#L6-L30

Installation
=============

Clone the repository::

    git clone git://github.com/steinwurf/waf.git

Since Waf is added as a git submodule, we need to run a couple
extra commands to get the Waf source code::

    cd waf
    git submodule init
    git submodule update

Building Waf
============

Build waf and include our custom tools::

    cd waf/waf
    python waf-light --make-waf --tools=compat15,`cd ../tools && find $PWD -type f -name '*.py' | tr "\n" "," | sed "s/,$//g"`,`cd ../python-semver && find $PWD -type f -name 'semver.py'`

This will produce a waf binary which we may copy into our projects.
Note that the path to the tools must be absolute.

Source code
===========

The modifications and additions to Waf are in the `src/wurf` folder. The
main files included by Waf is the `src/wurf/waf_entry_point.py`. This is a great
place to start to understand our additions to `Waf`.

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
        ctx.add_dependency(name='foo',
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

Add `--no-self-test` option
---------------------------
The self test will invoke a freshly built `waf` binary with the wscript of the
project. This we should also be able to replace the current `waf` binary with
a freshly built one.

One issue with this, is that the self test will use the network to clone the
needed dependencies. This makes the test slow. It would therefore be beneficial
to remove this test when running e.g. in a build system.

Add `--force-resolve` option
----------------------------
Certain resolvers utilize "shortcuts" such as using cached information about
dependencies to speed the resolve step. Providing this option should by-pass
such optimizations and do a full resolve - not relying on any form of cached
data.

Add `--no-resolve` option
-------------------------
As default the resolver will be invoked when configuring a waf project i.e.
invoking `python waf configure ...`. Depending on the number of dependencies
this may take some time to complete. This is problematic if an user is for
example re-configuring to change compiler.

Providing the `--fast-resolve` option should only invoke the resolvers for
dependencies that have not already been downloaded. Already downloaded
dependencies should be loaded from the cache.

Add support for `dependencies.json`
-----------------------------------
Providing third-party tooling to work with the dependencies, i.e. monitoring
the dependencies and sending push notifications when new versions are available
etc. will be a lot easier if dependencies are stored outside the wscript in
some easy to process data structure.

It is therefore recommended that users specify dependencies using the
`dependencies.json` file.

If needed it should still be possible to define the `resolve(...)` function
in the wscript. This should only be used in situations where some information
about a dependency is not know until runtime or when some computations are
needed to determine the dependency. In that case an user can define
`resolve(...)` and write the needed Python code.

To support both these ways of configuring we define the following "rules":

1. If an user specifies a `resolve(...)` function in the wscript the resolver.
   Will invoke only this (an existing `dependencies.json` will not be loaded
   automatically). The user may manually load the `dependencies.json` file using
   add_dependency_file(...) method on the resolve context.
2. If no `resolve(...)` function is specified, the resolve system will
   automatically look for and load the `dependencies.json` file.

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
dependencies of projects automatically.

```
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
```

Log output
==========

`waf` supports logging output in the tools and basic zone filtering. You can
use it as follows:

```
from waflib import Logs

...

def some_function(param_one, param_two):
    Log.debug('wurf: In some_function')

```

In the above example `wurf` is the zone so if you wIn our tools we use `wurf`



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
