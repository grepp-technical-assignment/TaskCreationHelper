#include <vector>

typedef long long int lld;

lld solution(lld a, lld b, lld c){
    std::vector<lld> wow_a(a, a), wow_b(b, b), wow_c(c, c);
    return a+b+c;
}