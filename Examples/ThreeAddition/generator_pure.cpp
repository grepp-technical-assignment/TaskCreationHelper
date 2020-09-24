#include "tchrand.hpp"

#include <iostream>
#include <vector>
#include <string>
#include <stdlib.h>

void generate(std::vector<std::string> genscript, 
              long long &a, long long &b, long long &c){
    long long max_value = atoll(genscript[0].c_str());
    a = TCH::randint<long long>(0, max_value);
    b = TCH::randint<long long>(0, max_value);
    c = TCH::randint<long long>(0, max_value);
}
