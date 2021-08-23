#include <vector>
#include <algorithm>

std::vector<int> solution(std::vector<int> arr){
    std::sort(arr.begin(), arr.end());
    return arr;
}