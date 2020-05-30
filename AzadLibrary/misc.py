"""
This module contains miscellaneous functions.
"""

# Standard libraries
import random
import time


def barLine(message: str, lineLength: int = 120) -> str:
    """
    Print `<==...== msg ==...==>`.
    """
    if not isinstance(lineLength, int) or lineLength <= 20:
        raise ValueError("Invalid value lineLength = %s" % (lineLength,))
    baseMessage = "<" + "=" * (lineLength - 2) + ">"
    # 2x + msglen = total len
    preOffset = (lineLength - len(message)) // 2 - 1
    if preOffset <= 2:
        raise ValueError("Too long message for given line length")
    returnMessage = baseMessage[:preOffset] + " " + message + " "
    return returnMessage + baseMessage[-(lineLength - len(returnMessage)):]


def longEndSkip(message: str, maxLength: int = 100) -> str:
    """
    Print `msg ...` if message is too long.
    """
    assert maxLength > 3
    lenMsg = len(message)
    if lenMsg <= maxLength:
        return message
    else:
        return message[:maxLength - 3] + "..."


def randomName(length: int):
    """
    Return random name using English letters and numbers.
    """
    random.seed(time.time_ns())
    alphabets = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"
    candidates = alphabets.lower() + alphabets.upper() + numbers
    return "".join(random.choices(candidates, k=length))


if __name__ == "__main__":
    print(longEndSkip(str([i for i in range(10**4)])))
