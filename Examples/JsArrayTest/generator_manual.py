def generate(args):
    t = int(args[0])
    if t == 1:
        d0 = 1234
        d1 = [1, 2, 3, 4, 1111, 2222, 3333, 4444]
        d2 = [
            [1, 2, 3, 4],
            [11, 22, 33, 44],
            [111, 222, 333, 444],
        ]
    
    return {'d0': d0, 'd1': d1, 'd2': d2}