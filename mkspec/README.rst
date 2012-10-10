The waf mkspecs
===============

We could like to easily create the possibility to control which
target platform, compiler and compiler setting that should
be used for a specific build. Waf already has efficient support for
configuring and customizing the tool-chain, this we will take
advantage of to create this feature.

The basic idea is to create **mkspecs** - the name was borrowed from the Qt
project which uses it for the same purpose.

Naming a mkspec
===============

An example of an mkspec file is: ``cxx-platform-cpu-compiler-custom options.py``

Where the options are specifying the following:

================ =====================================
 option           purpose
================ =====================================
 platform         specifies the platform that is used
 cpu              the instruction set used
 compiler         the compiler
 custom options   user defined options can be anything
================ =====================================

The following table shows some example of values:

============= ========= ============== ================
 platform       cpu      compiler       custom options
============= ========= ============== ================
 linux         x86       gxx            i7-avx
 windows       x86_64    gxx46          test-sse4
 blackberry    armv5te   clang
 ios                     clang31
 android                 msvc2010
 solaris                 msvc2012
 windowsphone            macport-gxx46
 mac
============= ========= ============== ================

Some examples of mkspecs are::

   cxx_linux-x86-gxx.py
   cxx_linux-x86_64-gxx46.py
   cxx_windows-x86-msvc2010.py
   cxx_windows-x86_x64-msvc2010.py
   cxx_windows-x86_x64-msvc2010-i7-avx.py

We will also allow values to be dropped e.g. ``cxx_linux-x86.py``
the our tool should auto detect a compiler to use. This means
that even ``cxx_linux.py`` is valid, here we will simply try
to auto-detect everything - waf already does this pretty well
so we just rely on that.




