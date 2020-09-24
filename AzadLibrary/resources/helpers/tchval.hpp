#ifndef __TCH_VAL_HEADER
#define __TCH_VAL_HEADER

#include <string>
#include <stdexcept>
#include "tchio.hpp"

namespace TCH{

    // Raise an error with msg if given condition is false.
    template<typename ... Args>
    inline void assert(bool condition, const std::string &message, Args ... args){
        if(!condition) throw std::runtime_error(format(message, args ...));
    }

}

#endif