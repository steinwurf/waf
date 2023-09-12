Steinwurf's Waf
===============
|Waf Python Tests| |Black| |Flake8|

.. |Waf Python Tests| image:: https://github.com/steinwurf/waf/actions/workflows/python-waf.yml/badge.svg
   :target: https://github.com/steinwurf/waf/actions/workflows/python-waf.yml

.. |Flake8| image:: https://github.com/steinwurf/waf/actions/workflows/flake.yml/badge.svg
    :target: https://github.com/steinwurf/waf/actions/workflows/flake.yml

.. |Black| image:: https://github.com/steinwurf/waf/actions/workflows/black.yml/badge.svg
      :target: https://github.com/steinwurf/waf/actions/workflows/black.yml

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle / resolve library dependencies. The goal is to
add functionality to Waf such that it can clone and download needed dependencies
automatically.

.. contents:: Table of Contents:
   :local:

License
-------
This project is under the same BSD license as the Waf project. The license text
can be found here: https://gitlab.com/ita1024/waf/blob/master/waf-light#L6-30

Building our custom Waf binary
------------------------------

Clone the repository::

    git clone https://github.com/steinwurf/waf.git

Build waf and include our custom tools::

    python waf configure
    python waf build

This will produce a waf binary in the ``build`` folder which we may copy into
our projects.

Tests
-----

To ensure that the tools work as intended way we provide a set of
tests. To run the tests invoke::

      python waf --run_tests

``--skip_network_tests``
........................

Passing ``--skip_network_tests`` will skip any unit tests which rely on network
connectivity.

To test the freshly built Waf binary, some unit test use network connectivity
to resolve dependencies. This makes the tests slow.

An example of such a test is the ``self_build`` test. The ``self_build`` test
will invoke a freshly built ``waf`` binary with the wscript used to build it -
yes very meta :)

``--test_filter``
.................

When working with a failing test or similar it may be beneficial to be able
to run only a selected set of tests. This can be achieved by passing a test
filter to pytest. The pytest test filter can be passed using the
``--test_filter``::

    python waf --test_filter="test_git"

The ``--test_filter`` string will by passed to the pytest ``-k``
option. See more information in the pytest documentation:
https://docs.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests

Running ``pytest --help`` will produce the following description of the
``-k`` option::

    -k EXPRESSION         only run tests which match the given substring
                           expression. An expression is a python evaluable
                           expression where all names are substring-matched
                           against test names and their parent classes. Example:
                           -k 'test_method or test_other' matches all test
                           functions and classes whose name contains
                           'test_method' or 'test_other'. Additionally keywords
                           are matched to classes and functions containing extra
                           names in their 'extra_keyword_matches' set, as well as
                           functions which have names assigned directly to them.

Fixing unit tests
.................

We use ``pytest`` to run the unit tests and integration tests. If some unit
tests fail, it may be helpful to go to the test folder and invoke the failing
waf commands manually.

Using our default configuration, pytest will create a local temporary folder
called ``pytest``  when running the tests. This can be overridden with the
``--pytest_basetemp`` option.

If a test uses the ``testdirectory`` fixture, then pytest will create a
subfolder matching the test function name. For example, if you have a test
function called ``test_empty_wscript(testdirectory)``, then the first invocation
of that test will happen inside ``pytest/test_empty_wscript0``.

Log output / debugging
......................

We use the logging system provided by waf. If you have an issue with the
resolve functionality, you can add the ``-v`` verbose flag (or ``-vvv``
to see all debug information). Alternatively you can use the
``--zones`` filter to see the resolver debug messages only::

    python waf configure -v --zones=resolve

The default zone printed by ``waf`` when adding the verbose flag ``-v`` is
``runner``, so if you want to see that also pass::

    python waf configure -v --zones=resolve,runner


Source code
-----------

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
.................

Code that uses/imports code from core Waf are prefixed with ``waf_``. This
makes it easy to see which files are pure Python and which provide the
integration points with Waf.


High-level overview
...................

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
   resolved and made available on our local file system (and we just load
   information about where they are located). Roughly speaking we
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
-----------------

Skipping resolve
................

Sometimes it is useful to skip the resolve step e.g. if you doing something
different than building the source code.

We've added an option to skip the resolve step::

    python waf --no_resolve ...

Specifying a dependency
.......................

There are two overall ways of specifying a dependency.

1. Using a ``resolve.json`` file.
2. Defining a ``resolve(...)`` function in the project's ``wscript``

A dependency is described using a number of key-value attributes. The following
defines the general dependency attributes:

Attribute ``name`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``name`` attribute is a string the assigns a human readable name to the
dependency::

    {
        "name": "my-pet-library",
        ...
    }

The name must be unique among all dependencies.

Attribute ``resolver`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``resolver`` attribute is a string that specifies the resolver type used to
download the dependency::

    {
        "name": "my-pet-library",
        "resolver": "git",
        ...
    }

Valid resolver types are: ``{"git" | "http"}``.

Attribute ``optional`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``optional`` attribute is a boolean which specifies that a dependency
is allowed to fail during the resolve step::

    {
        "name": "my-pet-library",
        "resolver": "git",
        "optional": true,
        ...
    }

If ``optional`` is not specified, it will default to ``false``.

Attribute ``recurse`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

This attribute specifies whether Waf should recurse into the dependency folder.

This is useful if the dependency is itself a Waf project. When recursing into
a folder Waf will look for a wscript in the folder and execute its commands.

Currently we will automatically (if recurse is ``true``), recurse into and execute
following Waf commands: (``resolve``, ``options``, ``configure``, ``build``)

As we also recurse into ``resolve`` it also enables us to recursively to resolve
the dependencies of our dependencies.

If you have a wscript where you would like to recurse dependencies for a custom
waf command, say ``upload``, then add the following to your wscript's
``upload`` function::

    def upload(ctx):
        ... your code
        # Now lets recurse and execute the upload functions in dependencies
        # wscripts.

        import waflib.extras.wurf.waf_resolve_context

        # Call upload in all dependencies (if it exists)
        waf_resolve_context.recurse_dependencies(self)

Example of attributes::

    {
        "name": "my-pet-library",
        "resolver": "git",
        "optional": true,
        "recurse": true,
        ...
    }

If ``recurse`` is not specified, it will default to ``true``.

Attribute ``internal`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``internal`` attribute is a boolean whether the dependency is internal to
the specific project. Lets make a small example, say we have two libraries
``libfoo`` which depends on ``libbar``. ``libbar`` has a dependency on ``gtest``
for running unit-tests etc. However, when resolving dependencies of ``libfoo``
we only get ``libbar`` because ``gtest`` is marked as ``internal`` to ``libbar``.
As illustrated by the small figure::

    +-------+
    |libfoo |
    +---+---+
        |
        |
        v
    +---+---+  internal   +--------+
    |libbar | +---------> | gtest  |
    +-------+             +--------+

Example of attributes::

    {
        "name": "my-pet-library",
        "resolver": "git",
        "optional": true,
        "recurse": true,
        "internal": true,
        ...
    }

If ``internal`` is not specified, it will default to ``false``.

Internal dependencies can be skipped from the top-level resolve step by
providing the ``--skip_internal`` option.

Attribute ``sources`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``sources`` attribute is a list containing URLs for the dependency. The URL
format depends on the resolver.

Example of attributes::

    {
        "name": "my-pet-library",
        "resolver": "git",
        "optional": true,
        "recurse": true,
        "internal": true,
        "sources": ["github.com/myorg/mylib.git"]
    }

Attribute ``post_resolve`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``post_resolve`` attribute is a list of steps to be performed after
successfully resolving a dependency.

The steps will be performed in the order they are specified.

Example of attributes::

    {
        "name": "my-pet-library",
        "resolver": "git",
        "optional": true,
        "recurse": true,
        "internal": true,
        "sources": ["github.com/myorg/mylib.git"],
        "post_resolve": [
            { "type": "run", "command": "tar -xvj file.tar" }
        ]
    }

The idea is to support different types of ``post_resolve`` steps,
currently we support the following:

1. ``run``: This type of post resolve step runs a ``command`` in the folder
   where the dependency has been resolved. The ``command`` can be either
   a string or list of strings i.e. the following is also valid::

       { "type": "run", "command": ["tar", "-xvj", "file.tar"] }

Attribute ``override`` (general)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

The ``override`` attribute is a boolean which forces specific settings
for a dependency. This attribute is useful if the same dependency is defined in
multiple projects and we want to force all projects to use the same version.

Example::

    +---------+  v1.1.0  +---------+
    |   app   +--------->| libbar  |
    +----+----+          +----+----+
         |                    |
         |                    | v2.0.0
         |                    v
         |     v2.0.0    +----+----+
         +-------------->| libfoo  |
                         +---------+

In the example above both ``app`` and ``libbar`` both depend on ``v2.0.0`` of
``libfoo``. Now lets say that the maintainer of ``app`` would like to experiment
with the new version of ``libfoo``. However, doing this results in a dependency
mismatch since ``libbar`` still depends on the old version.

To force a specific dependency we can use the ``override`` attribute (we use the
``git`` resolver here, you can read more about that below)::

    {
        "name": "libfoo"
        "resolver": "git",
        "method": "checkout",
        "checkout": "v3.0.0",
        "override": true,
        "sources": ["github.com/myorg/libfoo.git"]
        ...
    }

Setting ``override`` to ``true`` means that all projects will be forced to use
the specified options for a dependency. If ``override`` is not specified
it will default to ``false``.

Aside: The ``override`` attribute is similar to what can be locally acheived by
passing *user options* e.g. ``--libfoo-checkout=v3.0.0`` or
``--libfoo_path=...`` to ``./waf configure``. However, specifying the
``override`` attribute will allow such a change to be pushed to version control
etc.

Specifying a ``git`` dependency
...............................

The ``method`` attribute on a resolver of type ``git`` allows us to select
how the ``git`` resolver determines the correct version of the dependency to
use.

``checkout`` resolver
,,,,,,,,,,,,,,,,,,,,,

The simplest to use is the ``checkout`` method, which combined with the
``checkout`` attribute will use git to clone a specific tag, branch or SHA1
commit.::

    {
        "name": "somelib"
        "resolver": "git",
        "method": "checkout",
        "checkout": "my-branch"
        "sources": ["github.com/myorg/somelib.git"]
        ...
    }

``semver`` resolver
,,,,,,,,,,,,,,,,,,,

The ``semver`` method will use Semantic Versioning (www.semver.org) to select
the correct version (based on the available git tags). Using the ``major``
attribute we specific which major version of a dependency to use.  Example::

    On first resolve         Second resolve
    +-----------------------+-----------------------+
                            |
                   4.0.0    |                 4.0.0
                   4.0.1    |                 4.0.1
    Selected +---> 4.1.1    |                 4.1.1
                            |  Selected +---> 4.2.0
                            |                 5.0.0
                            |
                            +

On the initial resolve the newest available tag with major version 4 is
``4.1.1``. At a later point in time a we re-run resolve, this time new
versions of our dependency has been released and the newest is now ``4.2.0``.

Attributes::

    {
        "name": "someotherlib"
        "resolver": "git",
        "method": "semver",
        "major": 4,
        "sources": ["github.com/myorg/someotherlib.git"]
    }

Attribute ``pull_submodules`` (``git`` resolver)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

Using this attribute you can control whether submodules in a git dependency
should be cloned/pulled. Default is ``true`` which will clone/pull submodules if
found. To avoid cloning/pulling a submodule set ``pull_submodules: false``::

    {
        "name": "somelib"
        "resolver": "git",
        "method": "checkout",
        "checkout": "my-branch"
        "sources": ["github.com/myorg/somelib.git"],
        "pull_submodules": false
        ...
    }

Specifying a ``http`` dependency
...............................

Using the ``http`` resolver we can specify download dependencies via HTTP.

Attribute ``filename`` (``http`` resolver)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

Specify a filename of the downloaded dependency::

    {
        "name": "myfile"
        "resolver": "http",
        "filename": "somefile.zip",
        "sources": ["http://mydomain.com/myfile.zip"]
    }

The attribute is optional. If not specified the resolver will try to derive the
filename from the dependency URL, or the returned HTTP headers.

Attribute ``extract`` (``http`` resolver)
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

If the dependency is an archive (e.g. ``zip``, ``tar.gz``, etc.) the ``extract``
boolean specifies whether the archive should be extracted::

    {
        "name": "myfile"
        "resolver": "http",
        "extract": true,
        "sources": ["http://mydomain.com/myfile.zip"]
    }

If the ``extract`` attribute is not specified it defaults to ``false``.

Specifying dependencies (``resolve.json``)
.........................................

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

Specifying the dependency from the example above in ``resolve(...)`` of the
project's wscript::

    def resolve(ctx):

        ctx.add_dependency(
            name='waf-tools',
            resolver='git',
            method='semver',
            major=4,
            sources=['github.com/steinwurf/waf-tools.git'])

Resolve symlinks
................

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
are developing header-only projects side-by-side because you need to rebuild
the entire project if some header files changed. But if the dependencies
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

The ``--lock_versions`` option
..............................

The ``--lock_versions`` option will write ``lock_resolve_versions.json``
to the project folder. This file will describe the exact version information
about the project's dependencies.

The version information can be different for different resolvers:

- ``git`` resolvers will store the SHA1 commit id of the dependency.
- ``http`` resolvers will store the SHA1 sum of the downloaded dependency.

If the ``lock_resolve_versions.json`` is present, it will take precedence over all
resolvers besides the user options such as manually specifying checkout or
path.

You can commit the ``lock_resolve_versions.json`` file to git, e.g. when creating
a LTS (Long Term Support) release or similar where you want to pin the exact
versions for each dependency

As an example::

    # Writes / overwrites an existing lock_resolve_versions.json
    python waf configure --lock_versions

The ``--lock_paths`` option
...........................

The ``--lock_paths`` will write a ``lock_resolve_paths.json`` file in the project
folder. It behaves differently from the ``--lock_versions`` option in that it
will store the relative paths to the resolved dependencies. The typical
use case for this is to download all dependencies into a folder stored within
the project (default behavior) to make a standalone archive.

If the ``lock_resolve_paths.json`` is present, it will take precedence over
both the ``lock_resolve_versions.json`` and all other resolvers besides the user
resolvers besides the user options, such as manually specifying checkout or
path.

This makes it possible to easily create a standalone archive::

    python waf configure --lock_paths
    python waf standalone

Config file
...........

Using the ``--resolve_path`` option whenever doing a resolve or configure can be
cumbersome.
To combat this a config file can be used to override the default value for
this option.

The config file must be called ``.wurf_config``, and must be located in either
the project's directory or the user's directory. Note, the former takes priority
over the latter.

The following is an example of the content of a config file::

    [DEFAULT]
    resolve_path = ~/projects/dependencies

This config file will will override the default value for the resolve_path with
``~/projects/dependencies``.

Context helpers
---------------

We add various helpers to the Waf context objects. The following list is an
incomplete list of the helpers that are added.

``ctx.pip_compile(...)``
........................

Compiles a ``requirements_in`` file to a ``requirements_txt`` file. The
``requirements_in`` file is hashed and the hash is stored in the
``requirements_txt``.

The requirements_txt will be re-generated in two cases:

- The hash of the requirements_in file has changed.
- The requirements_txt file does not exist.


``ctx.create_virtualenv(...)``
..............................

Creates a virtualenv in a specified folder.


``ctx.ensure_build(...)``
..............................

Ensure that we've run the build step before running the current command.

``ctx.rewrite_file(...)``
.........................

Rewrites content of a file - useful for updating e.g. version numbers when
doing a release.

Future features
---------------

The following list contains the work items that we have identified as "cool"
features for the Waf dependency resolve extension.

Add ``--force-resolve`` option
..............................

Certain resolvers utilize "shortcuts" such as using cached information about
dependencies to speed the resolve step. Providing this option should by-pass
such optimizations and do a full resolve - not relying on any form of cached
data.

Print full log file on failure
..............................

To make error messages user-friendly the default is to redirect full tracebacks
(showing where an error originated), to the log files. However, if running on
a build system it is convenient to have the full traceback printed to the
terminal, this avoid us having to log into the machine an manually retrieve the
log file.

Dump resolved dependencies information to json.
...............................................

To support third party tooling working with information about an already
resolved dependency we implement the ``--dump-resolved-dependencies`` option.

This will write out information about resolved dependencies such as semver tag
chosen etc.
