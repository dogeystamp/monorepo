#!/usr/bin/env python3

"""
Tool to manually remove JPG corruption.

This takes an address and a region in bytes, and then writes random data in a
loop to that region. Type a specific value to go back to a previous iteration.

I was too lazy to write an argparse for this, so please set `addr`, `val_len`
and `file_name` below.

Also, duplicate the image file before running it through this!
"""

# region start
addr = 0x948
# region length in bytes
val_len = 2
file_name = "pic.jpg"

import mmap
import random

val = 0

max_val = 1 << (val_len * 8) - 1

while True:
    with open(file_name, "r+b") as file:
        with mmap.mmap(file.fileno(), 0) as mm:
            mm[addr : addr + val_len] = val.to_bytes(length=val_len)
            print(hex(val))
    inp = input()
    if inp == "":
        val = random.randint(0, max_val)
    else:
        val = int(inp, base=16)
