#ifndef __TCH_IO
#define __TCH_IO

#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>

namespace TCH{

    // Validate if given 2d array is perfect rectangle.
    template <typename t>
    inline bool validateRectangle(const std::vector<std::vector<t>> &val){
        for(size_t r=1; r<val.size(); r++) 
            if(val[r].size() != val[0].size()) return false;
        return true;
    }

    // Get single variable from input.
    template <typename t> 
    inline t get0d(std::istream &in){
        t val; in >> val;
        return val;
    }
    // Bool specialization of get0d.
    template <> 
    inline bool get0d<bool>(std::istream &in){
        std::string msg; in >> msg;
        if(msg != "true" && msg != "false")
            throw std::runtime_error("Boolean parsing failed");
        return msg == "true";
    }
    // String specialization of get0d.
    template <>
    inline std::string get0d<std::string>(std::istream &in){
        std::string result;
        int len = get0d<int>(in);
        while(len--){
            int lastchar = (char)get0d<int>(in);
            if(lastchar < 0 || lastchar > 255)
                throw std::runtime_error("Non-ascii character received");
            result += (char)lastchar;
        }
        return result;
    }

    // Get 1d array from input.
    template <typename t> 
    inline std::vector<t> get1d(std::istream &in){
        int size; in >> size;
        if(size < 0) throw std::runtime_error("Non-negative size");
        std::vector<t> result;
        while(size--) result.push_back(get0d<t>(in));
    }

    // Get 2d array from input.
    template <typename t> 
    inline std::vector<std::vector<t>> get2d(std::istream &in, bool validateRec){
        int size; in >> size;
        if(size < 0) throw std::runtime_error("Non-negative size");
        std::vector<std::vector<t>> result;
        while(size--) result.push_back(get1d<t>(in));
        if(validateRec) if(!validateRectangle<t>(result))
            throw std::runtime_error("Given array is not rectangle");
        return result;
    }

    // Put single variable to output.
    template <typename t> 
    inline void put0d(std::ostream &out, const t &val){
        out << val << '\n';
    }
    // Bool specialization of put0d.
    template <>
    inline void put0d<bool>(std::ostream &out, const bool &val){
        out << (val ? "true" : "false") << '\n';
    }
    // String specialization of put0d.
    template<>
    inline void put0d<std::string>(std::ostream &out, const std::string &val){
        put0d<size_t>(out, val.size());
        for(char c: val) put0d<int>(out, (int)c);
    }

    // Put 1d array to output.
    template <typename t> 
    inline void put1d(std::ostream &out, const std::vector<t> &val){
        put0d<size_t>(out, val.size());
        for(t element: val) put0d<t>(out, element);
    }

    // Put 2d array to output.
    template <typename t>
    inline void put2d(std::ostream &out, const std::vector<std::vector<t>> &val, bool validateRec){
        if(validateRec) if(!validateRectangle<t>(val))
            throw std::runtime_error("Given array is not rectangle");
        put0d<size_t>(out, val.size());
        for(t element: val) put1d<t>(out, element);
    }
};

#endif