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

inf = 99999999

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", default=1, type=int)
parser.add_argument("-e", "--end", default=inf, type=int)
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

uniq: dict[str, set[tuple[int, str]]] = {}
"""Character to index + word tuples mapping."""

prons: dict[str, set[str]] = {}
"""Character to pronunciations mapping."""

to_study: set[str] = set()
"""Characters to generate flashcards for."""

with open(args.input) as csv_file:
    reader = csv.reader(csv_file)
    writer = csv.writer(sys.stdout)

    iterator = (
        reader if args.single else itertools.islice(reader, args.start - 1, args.end)
    )

    for i, row in enumerate(iterator):
        word, pron, mean = row[:3]
        if args.single:
            if len(word) > 1:
                for sound, char in zip(pron.lower().split(), word):
                    if char not in uniq:
                        uniq[char] = set()
                        prons[char] = set()
                    uniq[char].add((i, word))
                    prons[char].add(sound)
                    if i < args.start - 1:
                        prev.add(char)
                    elif i < args.end and char not in prev:
                        to_study.add(char)
            else:
                single.add(word[0])
        else:
            writer.writerow([word, f"{pron} ({mean})"])

    if args.single:
        for char in to_study:
            if char not in single:
                writer.writerow(
                    [
                        char,
                        f"{', '.join(prons[char])} / {' '.join(c for _, c in sorted(uniq[char]))}",
                    ]
                )
