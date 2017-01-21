#include "foo.h"
#include <bar/bar.h>

std::string foo::whoooth()
{
    return std::string("foo") + bar::whoooth();
}
