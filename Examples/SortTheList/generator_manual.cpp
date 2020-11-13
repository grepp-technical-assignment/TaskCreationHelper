#include <vector>
#include <string>

void generate(std::vector<std::string> genscript, std::vector<int> &arr){

    arr.clear();
    for(std::string numstr: genscript) 
        arr.push_back(atoi(numstr.c_str()));
}