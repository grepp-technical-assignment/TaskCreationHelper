#include "tchrand.hpp"
#include <vector>
#include <string>

void generate(std::vector<std::string> genscript, std::vector<int> &arr){

    arr.clear();
    int maxlen = atoi(genscript[0].c_str());
    int maxnum = atoi(genscript[1].c_str());

    int n = TCH::randint(maxlen / 2, maxlen);
    for(int i=0; i<n; i++) arr.push_back(TCH::randint(-maxnum, maxnum));
    TCH::shuffle(arr.begin(), arr.end());
}