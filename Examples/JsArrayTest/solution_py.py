def solution(d0, d1, d2):
    return d0 + sum(d1) + sum([sum(i) for i in d2])