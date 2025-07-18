#!/bin/python3
"""
Note: xclip must be installed
       sudo apt-get install wl-clipboard

AI request #1:
You will be given a tech article, formatted the next way:
- paragraphs are separated by two "new line" chars, one "new line" should be just replaced with space and is for convinience;
- text has code sections that start with ``` and end with the same sequence;
Each line in the file starts with unique line id.
You need to find mistakes, typos and bad wording and correct them. You should not correct style or provide a better wording. Correct only critical mistakes described above.
You cant replace single words, the whole line needs to be replaced/correctd with a corrected one.
The output needs to be 2-columned file, unique line id of in the original line in the first column, the corrected variant of the line in the second column.
Columns should be separated with tab symbol.
Follow the line numbering stricktly: the output line number should physically match the number in input file. Section start sequences and empty lines count too!
Do not remove duplicate spaces.
"""

import sys
import argparse
import pyperclip

line_no_len = 6

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='AI-based text corrector',
    )

    parser.add_argument("article")
    parser.add_argument("-l", "--limit", default=50)
    args = parser.parse_args(sys.argv[1:])
    if not args.article.endswith(".art"):
        args.article += ".art"
    args.limit = int(args.limit or 50)

    # For some reason on Ubuntu i have to specify the clipboard type directly
    pyperclip.set_clipboard("wl-clipboard")

    with open(f"{args.article}/article.txt", "r") as article_file, open(f"{args.article}/article.correct", "w") as correct_file:
        line_no = 0
        while True:
            lines = []
            while line := article_file.readline():
                lines.append(f"{line_no:0{line_no_len}}\t{line}")
                line_no += 1
                if not line_no % args.limit:
                    break

            if not len(lines):
                break

            pyperclip.copy("".join(lines))
            input(f"{len(lines)} lines copied into clipboard. Copy corrected lines into clipboard and press Enter...")

            diff = [*filter(lambda x: len(x), pyperclip.paste().split("\n"))]
            print(f"{len(diff)} diff lines received")

            diff_idx = 0
            for l in lines:
                if diff_idx < len(diff) and l.startswith(diff[diff_idx][:line_no_len]):
                    correct_file.write(diff[diff_idx][line_no_len+1:] + "\n")
                    diff_idx += 1
                else:
                    correct_file.write(l[line_no_len+1:])


    print("Finished.")

