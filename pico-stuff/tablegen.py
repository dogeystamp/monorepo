# generate a flat binary tree for morse decoding

from functools import reduce

# https://stackoverflow.com/questions/71099952
encode_table = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "\\n": "-..-..",
    "\\b": ".-.-",
    "\\e": "..--",
    " ": "----",
}

maxLen = reduce(lambda x, y: max(x, y), [len(code) for code in encode_table.values()])

letters = ['*'] + ['*'] * 2**(maxLen + 1)

for sym, code in encode_table.items():
    idx = 1
    for lett in code:
        idx *= 2
        if lett == '-':
            idx += 1;
    letters[idx] = sym

print("".join(letters))
