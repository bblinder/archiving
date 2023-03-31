#!/usr/bin/env python3

import webvtt
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input file")
args = parser.parse_args()

def capitalize_first_letter(text):
    return re.sub(r'(^|\.\s+)(\w)', lambda m: m.group(1) + m.group(2).upper(), text)

input_file = args.input
output_title = input_file.split(".")[0]
output_file = f"{output_title}_formatted.txt"

vtt = webvtt.read(input_file)
transcript = ""

lines = []
for line in vtt:
    lines.extend(line.text.strip().splitlines())

previous = None
for line in lines:
    if line == previous:
       continue
    transcript += " " + line
    previous = line

transcript = transcript.strip()
transcript = capitalize_first_letter(transcript)

with open(output_file, "w") as f:
    f.write(transcript)