from random import randint as rnd

def generate(args):
    k = rnd(95000, 100000)
    m = rnd(500, 1000)
    n = rnd(500, 1000)

    d0 = rnd(2 ** 20, 2 ** 30)
    d1 = [rnd(2 ** 20, 2 ** 30) for _ in range(k)]
    d2 = [
        [rnd(2 ** 20, 2 ** 30) for _ in range(n)]
            for _ in range(m)
    ]
    
    return {'d0': d0, 'd1': d1, 'd2': d2}