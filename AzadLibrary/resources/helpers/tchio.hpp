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
        using thistype = t;

        inline static thistype get(std::istream &in){
            thistype value;
            in >> value;
            return value;
        }

        inline static void put(std::ostream &out, const thistype &data){
            out << data << '\n';
        }
    };

    // 3rd template of Data for string primitive value.
    template <> class Data<std::string, 0>{ public:
        using thistype = std::string;

        inline static thistype get(std::istream &in){
            std::string result;
            size_t size = Data<size_t, 0>::get(in);
            while(size--) result += (char)Data<int, 0>::get(in);
            return result;
        }

        inline static void put(std::ostream &out, const thistype &data){
            Data<size_t, 0>::put(out, data.length());
            for(char c: data) Data<int, 0>::put(out, (int)c);
        }
    };

    // 3rd template of Data for boolean primitive value.
    template <> class Data<bool, 0>{ public:
        using thistype = bool;

        inline static thistype get(std::istream &in){
            std::string msg; 
            in >> msg;
            if(msg != "true" && msg != "false")
                throw std::runtime_error("Boolean parsing failed");
            return msg == "true";
        }

        inline static void put(std::ostream &out, const thistype &data){
            out << (data ? "true" : "false") << '\n';
        }
    };

    // Primary template of Data for 1+ dimensional array.
    template <typename t, unsigned int dimension> class Data{ public:
        using prevtype = typename Data<t, dimension-1>::thistype;
        using thistype = std::vector<prevtype>;

        inline static thistype get(std::istream &in){
            size_t size = Data<size_t, 0>::get(in);
            thistype result;
            while(size--) result.push_back(Data<t, dimension-1>::get(in));
            return result;
        }

        inline static void put(std::ostream &out, const thistype &data){
            Data<size_t, 0>::put(out, data.size());
            for(prevtype element: data) Data<t, dimension-1>::put(out, element);
        }
    };
};

#endif