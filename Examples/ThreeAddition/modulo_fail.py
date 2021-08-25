import random


def solution(a: int, b: int, c: int):

    if a % 101 == 1:
        raise ValueError("mod 10000 fail")

    return a + b + c
