#include "bar.h"
#include <baz/baz.h>

std::string bar::whoooth()
{
    return baz::whoooth() + "bar";
}
