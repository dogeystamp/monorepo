#!/usr/bin/env python3

# See LICENSE file for copyright and license details.

import argparse

parser = argparse.ArgumentParser(
        description='''A script to encode coordinates from stdin to 4 words, or decode them.''')
parser.add_argument("dictionary", type=str,
help="The dictionary file to use. Each line is used as a word.")
parser.add_argument("--decode", "-d", action="store_true",
        help="Decode 4 words from stdin to coordinates")

args = parser.parse_args()

fp = open(args.dictionary, "r")
lines = fp.readlines()
# -1 for 0 indexing
nl = len(lines) - 1

if nl <= 0:
    raise(EOFError("Dictionary needs to have at least 2 words"))

def gw(ln):
    # Get a word from an index
    return lines[ln][:-1]

def gln(word):
    # Get the index from a word
    for i, line in enumerate(lines):
        if line.strip() == word.strip():
            return i

    raise(ValueError(f"No match for word {word} in {args.dictionary}."))

if not args.decode:
    lat, long = [float(i) for i in input().split()]

    if lat < -90 or lat > 90:
        raise(ValueError(f"Invalid latitude {lat}"))
    if long < -90 or long > 90:
        raise(ValueError(f"Invalid longitude {long}"))

    # Map to positive numbers
    lat += 90
    long += 180

    latV = lat/180*nl**2
    longV = long/360*nl**2

    print(gw(round(latV // nl)), end=" ")
    print(gw(round(latV % nl)), end=" ")
    print(gw(round(longV // nl)), end=" ")
    print(gw(round(longV % nl)))

else:
    words = input().split()
    lat = (gln(words[0]) * nl + gln(words[1])) / nl ** 2 * 180 - 90
    lon = (gln(words[2]) * nl + gln(words[3])) / nl ** 2 * 360 - 180

    print('{:.10}'.format(round(lat, 8)), end=" ")
    print('{:.9}'.format(round(lon, 8)))
