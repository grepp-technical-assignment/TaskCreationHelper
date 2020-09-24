def generate(args: list):

    index = int(args[0])
    if index == 1:
        a, b, c = 1, 2, 3
    elif index == 2:
        a, b, c = 0, 0, 0
    elif index == 3:
        a, b, c = 2, 0, -1
    else:
        raise ValueError("Invalid index")

    return {"a": a, "b": b, "c": c}
