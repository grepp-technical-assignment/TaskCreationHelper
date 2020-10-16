#ifndef __TCH_FORMAT_HEADER
#define __TCH_FORMAT_HEADER

#include <memory>
#include <string>
#include <stdexcept>

namespace TCH{
    
    // printf style format from https://stackoverflow.com/questions/2342162/stdstring-formatting-like-sprintf
    template<typename ... Args>
    inline std::string format(const std::string &message, Args ... args){
        size_t size = snprintf(nullptr, 0, message.c_str(), args ...) + 1; // Extra space for '\0'
        if(size <= 0) throw std::runtime_error("Error during formatting.");
        std::unique_ptr<char[]> buf(new char[size]); // Deletes automatically when destructs
        std::snprintf(buf.get(), size, message.c_str(), args ...);
        return std::string(buf.get(), buf.get() + size - 1); // Exclude '\0'
    }
}

#endif