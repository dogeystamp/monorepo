# dwg

dwg is a script that converts coordinates into four words and back, using a dictionary like Diceware.

## Usage

```
$ echo 55.5455 35.5434 | dwg.py dict.txt
supra skate oral canal
$ echo supra skate oral canal | dwg.py -d dict.txt
55.54550065 35.5433973
```

## Dictionaries

Reinhold's original [Diceware](https://theworld.com/~reinhold/diceware.wordlist.asc) dictionary is included as dict.txt, with numbers
and the PGP signature trimmed off. Any other newline-delimited text file will work as a dictionary file.
