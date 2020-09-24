def solution(a: int, b: int, c: int) -> int:

    s = 0

    def add(x: int):
        nonlocal s
        while x > 0:
            s += 1
            x -= 1

    add(a)
    add(b)
    add(c)
    return s
