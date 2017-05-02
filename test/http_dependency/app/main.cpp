// Copyright (c) Steinwurf ApS 2016.
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>
#include <vector>
#include <cstdint>

#include <endian/is_big_endian.hpp>

int main()
{
    if (endian::is_big_endian())
    {
       std::cout << "This machine is big endian." << std::endl;
    }
    else
    {
       std::cout << "This machine is little endian." << std::endl;
    }
}
