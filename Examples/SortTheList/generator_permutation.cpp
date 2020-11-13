#include "tchrand.hpp"
#include <vector>
#include <string>

void generate(std::vector<std::string> genscript, std::vector<int> &arr){

    arr.clear();
    int maxlen = atoi(genscript[0].c_str());
    int n = TCH::randint(maxlen / 2, maxlen);
    arr = TCH::generatePermutation(n);
}