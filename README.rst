Introduction
============

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle library dependencies and tool-chains.

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
main files included by Waf is the `src/wurf/wurf_entry_point.py`.

Tools
=====

Loadable Steinwurf tools should start with the ``wurf_`` prefix
to distinguish them from standard waf tools.

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
-------
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

License
=======
This project is under the same BSD license as the WAF Project. The license text
can be found here: https://github.com/waf-project/waf/blob/master/waf-light#L6-L30
