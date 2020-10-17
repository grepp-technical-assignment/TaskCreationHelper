#ifndef __TCH_IO_HEADER
#define __TCH_IO_HEADER

#include <iostream>
#include <vector>
#include <memory>
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

    // Primary template of Data for 1+ dimensional array.
    // Detail implementation will be revealed later.
    template <typename t, unsigned int dimension> class Data;

    // Secondary template of Data for zero dimensional primitive value.
    template <typename t> class Data<t, 0>{ public:
        using thisCppType = t;
        using thisCType = thisCppType;

        inline static thisCppType get(std::istream &in){
            thisCppType value;
            in >> value;
            return value;
        }

        inline static void put(std::ostream &out, const thisCppType &data){
            out << data << '\n';
        }

        inline static thisCType convert_cpp_c(const thisCppType &data){
            return data;
        }

        inline static thisCppType convert_c_cpp(const thisCType &data){
            return data;
        }

        inline static void superfree(thisCType ptr){} // Do nothing
    };

    // 3rd template of Data for string primitive value.
    template <> class Data<std::string, 0>{ public:
        using thisCppType = std::string;
        using thisCType = char*;

        inline static thisCppType get(std::istream &in){
            std::string result;
            size_t size = Data<size_t, 0>::get(in);
            while(size--) result += (char)Data<int, 0>::get(in);
            return result;
        }

        inline static void put(std::ostream &out, const thisCppType &data){
            Data<size_t, 0>::put(out, data.length());
            for(char c: data) Data<int, 0>::put(out, (int)c);
        }

        inline static thisCType convert_cpp_c(const thisCppType &data){
            char* ptr = new char[data.length() + 1];
            for(size_t i=0; i<data.length(); i++) ptr[i] = data[i];
            ptr[data.length()] = 0;
            return ptr;
        }

        inline static thisCppType convert_c_cpp(const thisCType &data){
            return std::string(data);
        }

        inline static void superfree(thisCType ptr){
            delete[] ptr;
        }
    };

    // 3rd template of Data for boolean primitive value.
    template <> class Data<bool, 0>{ public:
        using thisCppType = bool;
        using thisCType = bool;

        inline static thisCppType get(std::istream &in){
            std::string msg; 
            in >> msg;
            if(msg != "true" && msg != "false")
                throw std::runtime_error("Boolean parsing failed");
            return msg == "true";
        }

        inline static void put(std::ostream &out, const thisCppType &data){
            out << (data ? "true" : "false") << '\n';
        }

        inline static thisCType convert_cpp_c(const thisCppType &data){
            return data;
        }

        inline static thisCppType convert_c_cpp(const thisCType &data){
            return data;
        }

        inline static void superfree(thisCType ptr){} // Do nothing
    };

    // Primary template of Data for 1+ dimensional array.
    template <typename t, unsigned int dimension> class Data{ public:
        using prevCppType = typename Data<t, dimension-1>::thisCppType;
        using thisCppType = std::vector<prevCppType>;
        using prevCType = typename Data<t, dimension-1>::thisCType;
        using thisCType = prevCType*;

        // Parse data from given input stream and return.
        inline static thisCppType get(std::istream &in){
            size_t size = Data<size_t, 0>::get(in);
            thisCppType result;
            while(size--) result.push_back(Data<t, dimension-1>::get(in));
            return result;
        }

        // Put data to given output stream.
        inline static void put(std::ostream &out, const thisCppType &data){
            Data<size_t, 0>::put(out, data.size());
            for(prevCppType element: data) Data<t, dimension-1>::put(out, element);
        }

        // Convert C++ data structure into C array.
        inline static thisCType convert_cpp_c(const thisCppType &data){
            thisCType ptr = new prevCType*[data.size() + 1];
            for(size_t i=0; i<data.size(); i++)
                ptr[i] = Data<t, dimension-1>::convert_cpp_c(data[i]);
            ptr[data.size()] = NULL;
            return ptr;
        }

        // Convert C array into C++ data structure.
        inline static thisCppType convert_c_cpp(const thisCType &data){
            thisCppType vec;
            for(size_t i=0; data[i] != NULL; i++)
                vec.push_back(Data<t, dimension-1>::convert_c_cpp(data[i]));
            return vec;
        }

        // Free C pointer.
        inline static void superfree(thisCType ptr){
            for(size_t i=0; ptr[i] != NULL; i++)
                Data<t, dimension-1>::superfree(ptr[i]);
            delete[] ptr;
        }
    };
};

#endif