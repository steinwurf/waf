// Copyright (c) Steinwurf ApS 2016.
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>

#include <baz/baz.h>

int main()
{
    std::cout << "app" << std::endl;
    std::cout << "baz::whoooth" << baz::whoooth() << std::endl;
    return 0;
}
