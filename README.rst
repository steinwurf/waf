Introduction
============

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle library dependencies and toolchains.

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


Bundle dependencies
===================

The basic


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
directory where the tests failed and play around. Once you are done exit
the virtualenv by running::

  $ deactivate
