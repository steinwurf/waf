// Copyright (c) 2016 Steinwurf ApS
// All Rights Reserved
//
// Distributed under the "BSD License". See the accompanying LICENSE.rst file.

#include <iostream>
#include <algorithm>
#include <vector>
#include <cstdint>
#include <string>
#include <numeric>
#include <memory>

struct record
{
    std::string name;
    uint64_t id;
};

auto find_id(const std::vector<record>& people,
             const std::string& name)
{
    auto match_name = [&name](const record& r)
    {
        return r.name == name;
    };
    auto ii = std::find_if(people.begin(), people.end(), match_name);
    if (ii == people.end())
        return (uint64_t)0;
    else
        return ii->id;
}

void test_type_deduction()
{
    std::vector<record> roster =
        {
            {"mark",1}, {"bill",2}, {"ted",3}
        };
    std::cout << find_id(roster,"bill") << "\n";
    std::cout << find_id(roster,"ron") << "\n";
}

void test_generic_lambda()
{
    std::vector<int> ivec = { 1, 2, 3, 4};
    std::vector<std::string> svec =
        { "red", "green", "blue" };

    auto adder  = [](auto op1, auto op2) { return op1 + op2; };

    std::cout << "int result : "
              << std::accumulate(ivec.begin(),
                                 ivec.end(),
                                 0,
                                 adder)
              << "\n";
    std::cout << "string result : "
              << std::accumulate(svec.begin(),
                                 svec.end(),
                                 std::string(""),
                                 adder)
              << "\n";
}

void test_init_captures()
{
    std::unique_ptr<int> ptr(new int(10));
    auto lambda = [value = std::move(ptr)] {return *value;};

    std::cout << "captured value: " << lambda() << "\n";
}

void test_literals()
{
    auto integer_literal = 1'000'000;
    auto floating_point_literal = 0.000'015'3;
    auto binary_literal = 0b0100'1100'0110;

    std::cout << "Literals: " << integer_literal << " / "
              << floating_point_literal << " / "  << binary_literal << "\n";

    std::cout << "Output mask: "
              << 0b1000'0001'1000'0000
              << "\n";
    std::cout << "Proposed salary: $"
              << 300'000.00
              << "\n";
}

int main()
{
    test_type_deduction();

    test_generic_lambda();

    test_init_captures();

    test_literals();

    std::cout << "REACHED END OF TEST PROGRAM" << std::endl;

    return 0;
}
