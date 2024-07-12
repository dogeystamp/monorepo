# hanzi-flash

Generate flashcards in CSV format for a range of frequent hanzi words.

This is based on the
[hsk CSV](https://github.com/plaktos/hsk_csv)
repo, including common usage words graded by difficulty.
These form the vocabulary of the HSK (hanzi proficiency exam).

## usage

This script requires the HSK vocabulary in a CSV file.
The expected format is word, pronunciation in pinyin, and definition.
You may combine all levels into a single file as such:

```
git clone https://github.com/plaktos/hsk_csv
cd hsk_csv
cat hsk*.csv > all_hsk.csv
```

To use the script, put this `all_hsk.csv` file in the same directory, or pass the path explicitly with the `-i/--input` flag.
CSV output goes to stdout, which can be redirected to a file.
For example, this generates a flashcard deck for the entire HSK vocabulary:

```
python hanzi_flash.py -i ./all_hsk.csv > output.csv
```

## ranges

HSK's 6 levels have increasingly large vocabulary.
This script can help you divide this into more digestible chunks.
Specify the `-s/--start` and `-e/--end` options to only output a range of characters.
For example, the first 50 characters:

```
python hanzi_flash.py -s 1 -e 50
```

Or, the next 50:

```
python hanzi_flash.py -s 51 -e 100
```

Once generated, use your flashcard app's merge feature after importing both these decks.

## single character mode

HSK's vocabulary is in words, not in individual characters.
Pass the `-S/--single` flag to break up the words into characters.
The flashcard will have a single character, and the answer will be its pronunciations and example words containing it.
This is intended as a supplement to the regular word flashcard decks.

Single mode respects the range options above,
and only outputs new, unique, characters
that appear first in the given range.
It will also not duplicate flashcards for words that are single characters.

For example, take the following invocations, with and without single mode:

```
$ python hanzi_flash.py -s 17 -e 19
电脑,diàn nǎo (computer)
电视,diàn shì (television)
电影,diàn yǐng (movie)
$ python hanzi_flash.py -s 17 -e 19 --single
脑,nǎo / 电脑
视,shì / 电视
影,yǐng / 电影
```

Single mode only picks out the new characters (电 was learned before the given range `17-19`).
