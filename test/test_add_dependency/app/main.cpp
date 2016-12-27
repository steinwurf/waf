// Copyright (c) Steinwurf ApS 2016.
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>

#include <foo/foo.h>

int main()
{
    std::cout << "app" << std::endl;
    std::cout << "foo::whoooth" << foo::whoooth() << std::endl;
    return 0;
}
