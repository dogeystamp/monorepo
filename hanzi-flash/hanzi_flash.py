#!/usr/bin/env python3
"""
Generate flashcards for a range of frequent hanzi characters.

See attached README for more information.
"""

import csv
import itertools
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", default=1, type=int)
parser.add_argument("-e", "--end", default=99999999, type=int)
parser.add_argument("-i", "--input", default="all_hsk.csv", type=Path)
parser.add_argument(
    "-S",
    "--single",
    action="store_true",
    help="Output unique single characters instead of words.",
)
args = parser.parse_args()

prev: set[str] = set()
"""Characters from previous single character card decks."""

single: set[str] = set()
"""Already single characters."""

uniq: dict[str, set[str]] = {}
"""Character to words mapping."""

prons: dict[str, set[str]] = {}
"""Character to pronunciations mapping."""

with open(args.input) as csv_file:
    reader = csv.reader(csv_file)
    writer = csv.writer(sys.stdout)
    start = 0 if args.single else args.start - 1
    for i, row in enumerate(itertools.islice(reader, start, args.end)):
        word, pron, mean = row[:3]
        if args.single:
            if len(word) > 1:
                for sound, char in zip(pron.lower().split(), word):
                    if i < args.start - 1:
                        prev.add(char)
                    elif char not in prev:
                        if char not in uniq:
                            uniq[char] = set()
                            prons[char] = set()
                        uniq[char].add(word)
                        prons[char].add(sound)
            else:
                single.add(word[0])
        else:
            writer.writerow([word, f"{pron} ({mean})"])

    if args.single:
        for char in uniq:
            if char not in single:
                writer.writerow(
                    [char, f"{', '.join(prons[char])} / {' '.join(uniq[char])}"]
                )
