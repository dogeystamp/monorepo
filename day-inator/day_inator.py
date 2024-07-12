#!/usr/bin/env python
"""Guess the weekday of a random date.

For more information, search 'Doomsday algorithm'.

You may pass a date argument as YYYY-MM-DD (leading zeroes required).
Otherwise, a random date is generated.
"""

import datetime
import random
import sys

epsilon: int = 365 * 200
"""Maximum variation in days for the date compared to today."""

r = random.randint(-epsilon, epsilon)
"""Actual variation in days for the date compared to today."""

d: datetime.date = datetime.date.today() + datetime.timedelta(days=1) * r
"""Date to guess."""

if len(sys.argv) > 1:
    d = datetime.date.fromisoformat(sys.argv[1])


def guess(d: datetime.date) -> bool:
    """Prompt for guess.

    Returns True if guess is good.
    """
    try:
        ans: int = (int(input("Guess: ")) - 1) % 7
        if ans not in range(7):
            raise ValueError
    except ValueError:
        print("Invalid input.")
    else:
        if ans == d.weekday():
            return True
    return False


print("""
Day-Inator 2000
---------------

Use 1-7 for Mon-Sun. See script docstring for more information.
""")

print(d)

start = datetime.datetime.now()
fails: int = 0

while not guess(d):
    print("Wrong.")
    fails += 1

print("Correct.")

dur = (datetime.datetime.now() - start).seconds
print(f"Took {dur} seconds with {fails + 1} tr{'ies' if fails else 'y'}.")
