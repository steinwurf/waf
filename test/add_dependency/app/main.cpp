// Copyright (c) Steinwurf ApS 2016.
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>

#include <baz/baz.h>
#include <foo/foo.h>

#ifdef EXTRA
#include <extra/extra.h>
#endif

int main()
{
    std::cout << "app" << std::endl;
    std::cout << "foo::whoooth" << foo::whoooth() << std::endl;
    std::cout << "baz::whoooth" << baz::whoooth() << std::endl;

#ifdef EXTRA
    std::cout << "extra::cowabunga" << extra::cowabunga() << std::endl;
#endif
    return 0;
}
