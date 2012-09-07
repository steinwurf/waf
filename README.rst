Introduction
============

We use Waf as our build tool. However, before adding the Waf
file to the individual projects we first add some additional
tools to Waf.

These help us to handle library dependencies and toolchains.

Installation
=============

Clone the repository::

    git clone git://github.com/steinwurf/external-waf.git external-waf

Since Waf is added as a git submodule, we need to run a couple
extra commands to get the Waf source code::

    cd external-waf
    git submodule init
    git submodule update

Building Waf
============

Build waf and include our custom tools::

    cd external-waf/waf
    python waf-light --make-waf --tools=compat15,`cd ../tools && find $PWD -type f -name '*.py' | tr "\n" "," | sed "s/,$//g"`,`cd ../python-semver && find $PWD -type f -name 'semver.py'`

This will preduce a waf executable which we may copy into our projets.
Note that the path to the tools must be absolute.

Tools
=====

* waf_unit_test_v2 is a copy of the waf_unit_test tool. It contains
  support for failing builds when a unit test fails and support for
  running unit tests using a custom command template.

