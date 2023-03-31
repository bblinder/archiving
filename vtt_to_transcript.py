#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert a WebVTT subtitle file to a formatted-ish transcript.
"""

import argparse
import re

import webvtt

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input file")
args = parser.parse_args()


def capitalize_first_letter(text):
    """
    Capitalize the first letter of each sentence in a string.
    """
    return re.sub(r"(^|\.\s+)(\w)", lambda m: m.group(1) + m.group(2).upper(), text)


input_file = args.input
output_title = input_file.split(".")[0]
output_file = f"{output_title}_formatted.txt"

vtt = webvtt.read(input_file)
TRANSCRIPT = ""

lines = []
for line in vtt:
    lines.extend(line.text.strip().splitlines())

PREVIOUS = None
for line in lines:
    if line == PREVIOUS:
        continue
    TRANSCRIPT += " " + line
    PREVIOUS = line

TRANSCRIPT = TRANSCRIPT.strip()
TRANSCRIPT = capitalize_first_letter(TRANSCRIPT)

with open(output_file, "w", encoding='utf-8') as f:
    f.write(TRANSCRIPT)
