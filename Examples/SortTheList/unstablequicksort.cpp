#include <vector>
#include <random>

// Unstable Quick Sort.
void unstablesort(std::vector<int> &arr, std::mt19937_64 &mersenne){
    if(arr.size() <= 1) return;

    // Pick
    std::uniform_int_distribution<int> dist(0, (int)arr.size() - 1);
    int middle_idx = dist(mersenne);
    int middle = arr[middle_idx];

    // Split
    std::vector<int> lower, upper;
    for(int i=0; i<(int)arr.size(); i++){
        if(i == middle_idx) continue;
        else if(arr[i] < middle) lower.push_back(arr[i]);
        else upper.push_back(arr[i]);
    }

    // Divide and Conquer
    unstablesort(lower, mersenne);
    unstablesort(upper, mersenne);
    arr = lower;
    arr.push_back(middle);
    for(int num: upper) arr.push_back(num);
}

std::vector<int> solution(std::vector<int> arr){
    std::random_device rd;
    std::mt19937_64 mersenne{rd()};
    unstablesort(arr, mersenne);
    return arr;
}