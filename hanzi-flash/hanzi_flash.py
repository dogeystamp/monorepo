#!/usr/bin/env python3
"""
Generate flashcards for a range of frequent hanzi characters.

Based on https://github.com/ruddfawcett/hanziDB.csv
"""

import csv
import itertools
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", default=0, type=int)
parser.add_argument("-e", "--end", default=99999999, type=int)
parser.add_argument("-O", "--output", default="hanzi_flash.csv", type=Path)
parser.add_argument("-i", "--input", default="hanzi_db.csv", type=Path)
args = parser.parse_args()

with open(args.input) as csv_file:
    reader = csv.reader(csv_file)
    with open(args.output, "w") as outp_file:
        writer = csv.writer(outp_file)
        for row in itertools.islice(reader, args.start, args.end + 1):
            writer.writerow([row[1], f"{row[2]} ({row[3]})"])
