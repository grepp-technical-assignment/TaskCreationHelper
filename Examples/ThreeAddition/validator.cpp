#include "tchval.hpp"

void validate(long long a, long long b, long long c){
    const long long limit = 1'000'000'000'000'000'000LL;
    TCH::assert(0 <= a && a <= limit, "a = %lld (out of range)", a);
    TCH::assert(0 <= b && b <= limit, "b = %lld (out of range)", b);
    TCH::assert(0 <= c && c <= limit, "c = %lld (out of range)", c);
}