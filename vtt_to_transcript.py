#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert a WebVTT subtitle file to a formatted-ish transcript.
Useful for summarization and other NLP tasks.

Usage:
    python3 vtt_to_transcript.py <youtube_url or vtt_file>
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path

from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def download_vtt(url: str) -> str:
    """
    Download a VTT file from YouTube. Default: en-US.
    """
    subtitle_formats = [
        "en",
        "en-US",
        "en-en",
    ]

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": subtitle_formats,
        "subtitlesformat": "vtt",
        "outtmpl": "%(title)s.%(ext)s",
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info["title"]

        # Download subtitles
        available_subtitles = info["requested_subtitles"]

        for subtitle_format in subtitle_formats:
            if subtitle_format in available_subtitles:
                ydl_opts["subtitleslangs"] = [subtitle_format]
                with YoutubeDL(ydl_opts) as ydl_download:
                    ydl_download.download([url])
                output_name = f"{title}.{subtitle_format}.vtt"
                return output_name

    return None


def capitalize_first_letter(text: str) -> str:
    """
    Capitalize the first letter of each sentence in a string.
    """
    return re.sub(r"(^|\.\s+)(\w)", lambda m: m.group(1) + m.group(2).upper(), text)


def remove_duplicate_lines(lines: list) -> str:
    """
    Remove duplicate lines in a string.
    """
    unique_lines = []
    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)
    return unique_lines


def main():
    """
    Main function.
    """
    try:
        import webvtt
    except ImportError:
        raise ImportError("Please install webvtt-py: pip install webvtt-py")

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input file")
    args = parser.parse_args()

    youtube_domains = [
        "youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "m.youtube.com",
    ]

    # if input_file is a YouTube URL, download the VTT file
    if any(domain in args.input for domain in youtube_domains):
        input_file = download_vtt(args.input)
        if input_file is None:
            logging.error("No subtitles available for the requested language.")
            sys.exit(1)
    else:
        input_file = args.input

    output_title = input_file.split(".")[0]
    output_file = f"{output_title}_formatted.txt"

    vtt = webvtt.read(input_file)
    transcript = ""

    lines = [
        line.strip()
        for caption in vtt
        for line in caption.text.strip().splitlines()
        if line != transcript[-len(line) :]
    ]

    # remove duplicate lines
    lines = remove_duplicate_lines(lines)

    transcript = " ".join(lines)
    transcript = capitalize_first_letter(transcript)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)

    # after transcript is generated, delete the VTT files
    if any(domain in args.input for domain in youtube_domains):
        os.remove(input_file)
        # remove all VTT files
        for file in os.listdir():
            if file.endswith(".vtt"):
                os.remove(file)

    # print the full path of the output file
    logging.info(f"Transcript saved to: {Path(output_file).resolve()}")


if __name__ == "__main__":
    main()
