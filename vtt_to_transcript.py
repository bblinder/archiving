#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert a WebVTT subtitle file to a formatted-ish transcript.
Useful for summarization and other NLP tasks.

Usage:
    python3 vtt_to_transcript.py <video_url or vtt_file>
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
import validators

from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def download_vtt(url: str) -> str:
    """
    Download a VTT file using yt-dlp. Default: en-US.
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
        available_subtitles = info.get("requested_subtitles", {})

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


def remove_duplicate_lines(lines: list) -> list:
    """
    Remove duplicate lines in a list.
    """
    return list(dict.fromkeys(lines))


def validate_input(input: str) -> str:
    """
    Validate input.
    """
    http_regex = re.compile(r"^https?://")

    if http_regex.match(input):
        if not validators.url(input):
            logging.error("Invalid URL.")
            sys.exit(1)
        else:
            return download_vtt(input)
    elif Path(input).exists():
        return input
    else:
        logging.error("Invalid input.")
        sys.exit(1)


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

    # Validate input and get the VTT file path
    input_file = validate_input(args.input)

    output_title = input_file.split(".")[0]
    output_file = f"{output_title}_formatted.txt"

    vtt = webvtt.read(input_file)
    transcript = ""

    lines = [
        line.strip()
        for caption in vtt
        for line in caption.text.strip().splitlines()
        if line not in transcript[-len(line):]
    ]

    # Remove duplicate lines
    lines = remove_duplicate_lines(lines)

    transcript = " ".join(lines)
    transcript = capitalize_first_letter(transcript)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)

    # After the transcript is generated, delete the VTT files
    if input_file.endswith(".vtt"):
        os.remove(input_file)
        # Remove all VTT files
        for file in os.listdir():
            if file.endswith(".vtt"):
                os.remove(file)

    # Print the full path of the output file
    logging.info(f"Transcript saved to: {Path(output_file).resolve()}")
    logging.info("Done.")

if __name__ == "__main__":
    main()