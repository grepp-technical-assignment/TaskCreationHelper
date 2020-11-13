#include <vector>
#include <algorithm>

std::vector<int> solution(std::vector<int> arr){
    for(int i=0; i<(int)arr.size(); i++){
        int minidx = std::min_element(arr.begin() + i, arr.end()) - arr.begin();
        if(i != minidx) std::swap(arr[i], arr[minidx]);
    }
    return arr;
}