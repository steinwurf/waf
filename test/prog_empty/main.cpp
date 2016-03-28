#include <gtest/gtest.h>
#include <stdint.h>
#include <ctime>

// Tests 2+2 equals 4
TEST(TwoPlusTwo, Addition)
{
  EXPECT_EQ(2+2, 4);
}


GTEST_API_ int main(int argc, char **argv)
{
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}


