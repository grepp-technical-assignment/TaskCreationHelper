def validate(a: int, b: int, c: int):
    limit = 10 ** 18
    assert 0 <= a <= limit
    assert 0 <= b <= limit
    assert 0 <= c <= limit
