#include "tchval.hpp"
#include <vector>

void validate(std::vector<int> arr){

    TCH::assert(1 <= (int)arr.size() && (int)arr.size() <= 1'000'000,
        "arr size = %d (out of range)", (int)arr.size());
    
    const int limit = 1'000'000'000;
    for(int i=0; i<(int)arr.size(); i++)
        TCH::assert(-limit <= arr[i] && arr[i] <= limit,
            "arr[%d] = %d (out of range)", i, arr[i]);
}