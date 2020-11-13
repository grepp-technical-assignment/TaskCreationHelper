#ifndef __TCH_RAND_HEADER
#define __TCH_RAND_HEADER

#include <vector>
#include <string>
#include <algorithm>
#include <random>
#include <stdexcept>

namespace TCH{

    // Random generator engine
    inline std::mt19937_64 mersenneTwister;

    // Set seed of engine. This should be called before generator function.
    inline void seed(const std::vector<std::string> &genscript){
        if(genscript.empty()) throw std::runtime_error("Empty genscript given");

        // Join all strings in genscript
        std::string joined;
        for(std::string arg: genscript){
            joined += arg; 
            joined += '|';
        } joined.pop_back();

        // Make seed sequence and apply
        std::seed_seq seed(joined.begin(), joined.end());
        mersenneTwister.seed(seed);
    }

    // Return uniform integer on range [l, r].
    template <typename intlike> 
    inline intlike randint(intlike l, intlike r){
        std::uniform_int_distribution<intlike> distrib(l, r);
        return distrib(mersenneTwister);
    }

    // Return uniform real number on range [l, r).
    template <typename reallike> 
    inline reallike randreal(reallike l, reallike r){
        std::uniform_real_distribution<reallike> distrib(l, r);
        return distrib(mersenneTwister);
    }

    // Return True or False randomly.
    inline bool randbool(){
        std::uniform_int_distribution<int> distrib(0, 1);
        return (bool)distrib(mersenneTwister);
    }

    // Shuffle between two iterators.
    template <class iterator> 
    inline void shuffle(iterator begin, iterator end){
        int size = std::distance<iterator>(begin, end);
        if(size < 0) 
            std::runtime_error("End iterator is at before begin iterator");
        else if(size == 0) return;
        
        for(int i = size-1; i >= 0; i--)
            std::swap(begin[i], begin[randint<int>(0, i)]);
    }

    // Generate random permutation with given size.
    inline std::vector<int> generatePermutation(int size, int offset = 0){
        if(size <= 0) throw std::runtime_error("Non-positive size given");
        std::vector<int> result(size);
        for(int i=0; i<size; i++) result[i] = offset + i;
        shuffle(result.begin(), result.end());
        return result;
    }
};

#endif