import random


def solution(a: int, b: int, c: int):

    mod = 101
    if a % mod == mod - 1:
        raise ValueError("mod %d fail" % (mod,))

    return a + b + c
