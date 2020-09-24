#ifndef __TCH_RAND_HEADER
#define __TCH_RAND_HEADER

#include <vector>
#include <string>
#include <algorithm>
#include <random>
#include <stdexcept>

namespace TCH{

    // Random generator engine
    static std::mt19937_64 mersenneTwister;

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

    // Generate random permutation with given size.
    inline std::vector<int> generatePermutation(int size){
        if(size <= 0) throw "Non-positive size given";
        std::vector<int> result(size);
        for(int i=0; i<size; i++) result[i] = i;
        for(int i1=size-1; i1>=0; i1--){
            int i2 = randint<int>(0, i1);
            if(i1 != i2) std::swap(result[i1], result[i2]);
        } return result;
    }

    // Shuffle between two iterators.
    template <class iterator> 
    inline void shuffle(iterator begin, iterator end){
        int size = std::distance<iterator>(begin, end);
        if(size < 0) throw "End iterator is at before begin iterator";
        else if(size == 0) return;
        
        // arr[x] := arr[perm[x]]
        std::vector<int> perm = generatePermutation(size);
        std::vector<bool> moved(size, false);

        // Iterate
        for(iterator it = begin; it != end; it++){
            if(moved[it - begin]) continue;

            // itprev denotes arr[x], itafter denotes arr[perm[x]]
            iterator itprev = it, itafter = begin + perm[itprev - begin];
            while(itafter != it){
                moved[itprev - begin] = true;
                std::iter_swap(itprev, itafter);
                itprev = itafter;
                itafter = begin + perm[itafter - begin];
            }
            moved[itprev - begin] = true;
        }
    }
};

#endif