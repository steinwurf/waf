// Copyright (c) Steinwurf ApS 2016.
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>
#include <vector>
#include <cstdint>

#include <prettyprint.hpp>

int main()
{
    std::vector<uint32_t> data;
    data.push_back(1);
    data.push_back(2);
    data.push_back(3);

    std::cout << "vector: " << data << std::endl;
}
