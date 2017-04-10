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

This will produce a waf binary in the ``build`` folder which we may copy into
our projects.

Tests
=====

To ensure that the tools work as intended way we provide a set of
tests. To run the tests invoke::

      python waf --run_tests

``--skip_network_tests``
------------------------
Passing ``--skip_network_tests`` will skip any unit tests which rely on network
connectivity.

To test the freshly built Waf binary, some unit test use network connectivity
to resolve dependencies. This makes the tests slow.

An example of such a test is the ``self_build`` test. The ``self_build`` test
will invoke a freshly built ``waf`` binary with the wscript used to build it -
yes very meta :)

Fixing unit tests
-----------------

We use ``pytest`` to run the unit tests and integration tests. If some unit
tests fail, it may be helpful to go to the test folder and invoke the failing
waf commands manually.

Using our default configuration, pytest will create a local temporary folder
called ``pytest``  when running the tests. This can be overridden with the
``--pytest_basetemp`` option.

If a test uses the ``test_directory`` fixture, then pytest will create a
subfolder matching the test function name. For example, if you have a test
function called ``test_empty_wscript(test_directory)``, then the first invocation
of that test will happen inside ``py_test/test_empty_wscript0``.

Log output / debugging
----------------------

We use the logging system provided by waf. If you have an issue with the
resolve functionality, you can add the ``-v`` verbose flag (or ``-vvv``
to see all debug information). Alternatively you can use the
``--zones`` filter to see the resolver debug messages only::

    python waf configure -v --zones=resolve

The default zone printed by ``waf`` when adding the verbose flag ``-v`` is
``runner``, so if you want to see that also pass::

    python waf configure -v --zones=resolve,runner



Source code
===========

The modifications and additions to Waf are in the ``src/wurf`` folder. The
main file included by Waf is the ``src/wurf/waf_entry_point.py``. This is a great
place to start to understand our additions to ``Waf``.

Waf will load this file automatically when starting up, which is acheived using
the ``--prelude`` option of Waf. Described in the Waf book:
https://waf.io/book/#_customization_and_redistribution.

The location of the source files is a bit tricky, as Waf will move these files
in the ``src/wurf`` folder to ``waflib.extras.wurf``. In the core files, we use
the relative include (``from . import xyz``). When running the unit tests,
we add the ``src`` to ``PYTHONPATH``, so the tested classes are imported like
this::

    from wurf.xyz import Xyz

Waf specific code
-----------------

Code that uses/imports code from core Waf are prefixed with ``waf_``. This
makes it easy to see which files are pure Python and which provide the
integration points with Waf.


High-level overview
-------------------

The main modification added to the standard Waf flow of control, is the addition
of the `ResolveContext`. At a high-level this looks as follows::

    ./waf ....

             +
             |
          1. |
             |
    +--------v--------+      2.      +----------------+
    |                 +------------> |                |
    | OptionsContext  |              | ResolveContext |
    |                 | <----------+ |                |
    +-----------------+      3.      +----------------+
             |
          4. |
             |
    +--------v--------+
    | ConfigureContext|
    | BuildContext    |
    | ....            |
    +-----------------+

Lets outline the different steps:

1. The user invokes the waf binary in the project folder, internally Waf will
   create the ``OptionsContext`` to recurse out in user's ``wscript`` files and collect
   the project options.
2. However, before that happens we will create the ``ResolveContext`` which is
   responsible for *making sure declared dependencies are available*. The resolve
   step has two main modes of operation "resolve" and "load". In the "resolve"
   mode we will try to fetch the needed dependencies e.g. via `git clone` or
   other ways. In the "load" mode we expect dependencies to have already been
   resolved and made available on our local file system. Roughly speaking we
   will be in "resolve" mode when the users uses the "configure" command i.e.
   ``python waf configure ...`` and otherwise in the "load" mode.
3. In both cases the ``ResolveContext`` makes a dependency available by producing
   a path to that dependency. That can later be used on other contexts etc. E.g.
   If the dependency declares that it is recursable, we will automatically
   recurse it for options, configure and build.
4. After having executed the ``OptionsContext`` and collected all options etc.
   control is passed to the next Waf / user-defined context. At this point
   path to dependencies are still available in the global
   `dependency_cache` dictionary in ``waf_resolve_context.py``.


Resolver features
=================

Specifying a dependency(``resolve.json``)
-----------------------------------------

Providing third-party tooling to work with the dependencies, i.e. monitoring
the dependencies and sending push notifications when new versions are available
etc. is a lot easier if dependencies are stored outside the ``wscript`` in an
easy to process data structure.

It is therefore recommended that users specify dependencies using a
``resolve.json`` file.

A simple example for a ``resolve.json`` file specifying a single git semver
dependency::

    [
        {
            "name": "waf-tools",
            "resolver": "git",
            "method": "semver",
            "major": 4,
            "sources": ["github.com/steinwurf/waf-tools.git"]
        }
    ]

If needed it is still possible to define the ``resolve(...)`` function
in the ``wscript``. This should only be used in situations where some information
about a dependency is not known until runtime or when some computations are
needed to determine some information regarding a dependency. In that case, the
user can define the ``resolve(...)`` function in the ``wscript`` and write the
needed Python code.

To support both these configuration methods, we define the following "rules":

1. The user defined ``resolve(...)`` function will always be called before
   loading a ``resolve.json`` file (if present).
2. It is valid to mix both methods to define dependencies.

The ``recurse`` attribute
-------------------------
This option specifies whether waf should recurse into the dependency folder.
The default value of ``recurse`` is ``True``.

This is useful if the dependency is itself a waf probject. When recursing into
a folder waf will look for a wscript in the folder and execute its commands.

Currently we will automatically (if recurse is True), recurse into and execute
following waf commands: (resolve, options, configure, build)

If you have a wscript where you would like to recurse dependencies for a custom
waf command, say ``upload``, then add the following to your wscript's
``upload`` function::

    def upload(ctx):
        ... your code
        # Now lets recurse and execute the upload functions in dependencies
        # wscripts.

        import waflib.extras.wurf.waf_resolve_context

        # Call upload in all dependencies
        waf_resolve_context.recurse_dependencies(self)

Resolve symlinks
----------------
The purpose of this feature is to provide stable locations in the file system
for the downloaded dependencies.

By default, several folders will be created during the process of resolving
dependencies. Several projects can share the same folder for resolved
dependencies (this is controlled using the ``--resolve_path`` option). To avoid
confusing/error-prone situations the folders are considered immutable. This
results in some overhead, as the dependency paths will change as new
versions of them become available. E.g if the ``gtest`` dependency is currently
located under ``/path/to/gtest-1.6.7-someh4sh``, as soon as version ``1.6.8`` is
released and the user re-runs ``python waf configure`` the path may be
updated to ``/path/to/gtest-1.6.8-someh4sh`` as the resolver noticed the new
version.

This is problematic e.g. for IDE configurations where the user needs to manually
go and update the path in the IDE to the new location.

Moreover, Waf fails to recognize changes in dependency include files
if they are located outside the project root. This is very annoying if you
are developing header-only projects side-by-side, because you need to rebuild
the entire project if some header file changed. But if the dependencies
are accessed through a symlink within the project, then Waf will be able to
track the changes in all the include files.

To avoid these problems, we created the ``resolve_symlinks`` local folder in
the project root that contains symlinks to the resolved dependencies. The
path can be changed with the ``--symlinks_path`` option.

For the previous example we would see the following in the ``resolve_symlinks``
folder::

    $ ls -la resolve_symlinks/
    total 0
    lrwxrwxrwx 1 usr usr 29 Feb 20 20:55 gtest -> /path/to/gtest-1.6.7-someh4sh

After re-running ``python waf configure ...``::

    $ ls -la resolve_symlinks/
    total 0
    lrwxrwxrwx 1 usr usr 29 Feb 20 20:57 gtest -> /path/to/gtest-1.6.8-someh4sh

The ExistingTagResolver and the ``--fast_resolve`` option
---------------------------------------------------------

Running ``python waf configure`` can take a very long time if the project
has a lot of dependencies. In the past, we had to endure a long delay when
re-configuring even if the dependencies have not changed at all, or if we just
wanted to change the compiler,

To solve that problem, we implemented the ExistingTagResolver that checks
if a newer, compatible version of a Steinwurf dependency project has been
released using the tag database here:
http://files.steinwurf.com/registry/tags.json

If the latest compatible tag is already available in our
``resolved_dependencies`` folder, then the resolver will use that tag without
running any git operations, so the configure operation can be extremely fast.
Moreover, if the same ``resolved_dependencies`` folder is used for multiple
projects that have similar dependencies, then it is guaranteed that we download
a new version of some dependency exactly once.

The ExistingTagResolver is enabled by default.

For an even faster experience, we also provide the ``--fast_resolve`` option
that should only invoke the resolvers for dependencies that have not been
downloaded. Already downloaded dependencies should be loaded from the cache.

``--fast_resolve`` can also be combined with other resolver options.
For example, we can manually set the path of the ``foo`` dependency and use
``--fast_resolve`` to load all other dependencies from cache::

    python waf configure --foo-path /tmp/foo --fast_resolve


The ``--lock_versions`` option
------------------------------

The ``--lock_versions`` option will write ``lock_resolve.json`` to the project
folder. This file will describe the exact version information about the
project's dependencies.

The version information can be different for different resolvers:

- ``git`` resolvers will store the SHA1 commit id or the semver tag of the
  dependency.
- ``http`` resolvers will store the SHA1 sum of the downloaded dependency.

If the ``lock_resolve.json`` is present, it will take precedence over all
resolvers besides the user optionsm such as manually specifying checkout or
path.

You can commit the ``lock_resolve.json`` file to git, e.g. when creating
a LTS (Long Term Support) release or similar where you want to pin the exact
versions for each dependency

As an example::

    # Writes / overwrites an existing lock_resolve.json
    python waf configure --lock_versions

The ``--lock_paths`` option
---------------------------

The ``--lock_paths`` will write a ``lock_resolve.json`` file in the project
folder. It behaves differently from the ``--lock_versions`` option in that it
will store the relative paths to the resolved dependencies. The typical
use case for this is to download all dependencies into a folder stored within
the project (default behavior) in order to make a standalone archive.

If the ``lock_resolve.json`` is present, it will take precedence over all
resolvers besides the user options, such as manually specifying checkout or
path.

This makes it possible to easily create a standalone archive::

    python waf configure --lock_paths
    python waf standalone



Future features
===============

The following list contains the work items that we have identified as "cool"
features for the Waf dependency resolve extension.

Add ``--force-resolve`` option
----------------------------
Certain resolvers utilize "shortcuts" such as using cached information about
dependencies to speed the resolve step. Providing this option should by-pass
such optimizations and do a full resolve - not relying on any form of cached
data.

Print full log file on failure
------------------------------
To make error messages user-friendly the default is to redirect full tracebacks
(showing where an error originated), to the log files. However, if running on
a build system it is convenient to have the full traceback printed to the
terminal, this avoid us having to log into the machine an manually retrieve the
log file.

Dump resolved dependencies information to json.
-----------------------------------------------
To support third party tooling working with information about an already
resolved dependency we implement the ``--dump-resolved-dependencies`` option.

This will write out information about resolved dependencies such as semver tag
chosen etc.
