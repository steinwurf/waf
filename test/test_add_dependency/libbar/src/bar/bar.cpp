#include "bar.h"
#include <foo/bar.h>

std::string bar::whoooth()
{
    return foo::whoooth() + "baaaar";
}
