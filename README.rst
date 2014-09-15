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




