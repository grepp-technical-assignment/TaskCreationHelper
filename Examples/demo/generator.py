import random


def generate(args: list):
    limit = int(args[0])
    return {
        "a": random.randint(-limit, limit),
        "b": random.randint(-limit, limit),
    }
