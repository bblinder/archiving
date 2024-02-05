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
import contextlib
from pathlib import Path

import validators
from yt_dlp import YoutubeDL

try:
    import webvtt
except ImportError:
    raise ImportError("Please install webvtt-py: pip install webvtt-py")

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


@contextlib.contextmanager
def suppress_output():
    """
    A context manager to redirect stdout and stderr to devnull
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def sanitize_title(title: str) -> str:
    """
    Sanitize a title by removing special characters and replacing with underscores.
    """
    if re.search(r"[\w\-]+", title):
        sanitized_title = re.sub(r"[^\w\-]+", "_", title)
        sanitized_title = re.sub(r"_+", "_", sanitized_title)
        return sanitized_title
    return title


def download_vtt(url: str) -> str:
    """
    Download a VTT file using yt-dlp. Default: en-US.
    """

    subtitle_formats = [
        "en",
        "en-US",
        "en-en",
    ]

    with suppress_output():
        with YoutubeDL({"skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info["title"]

            sanitized_title = sanitize_title(title)

        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": subtitle_formats,
            "subtitlesformat": "vtt",
            "quiet": True,
            "logger": None,
            "outtmpl": f"{sanitized_title}.%(ext)s",
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            available_subtitles = info.get("requested_subtitles", {})

            for subtitle_format in subtitle_formats:
                if subtitle_format in available_subtitles:
                    ydl_opts["subtitleslangs"] = [subtitle_format]
                    with YoutubeDL(ydl_opts) as ydl_download:
                        ydl_download.download([url])
                    output_name = f"{sanitized_title}.{subtitle_format}.vtt"
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


def restore_punctuation(text: str) -> str:
    from deepmultilingualpunctuation import PunctuationModel

    model = PunctuationModel()
    return model.restore_punctuation(text)

def main():
    """
    Main function.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input file or URL.")
    parser.add_argument(
        "-d",
        "--delete",
        help="Delete the original .VTT file after processing.",
        action="store_true",
    )
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
        if line not in transcript[-len(line) :]
    ]

    # Remove duplicate lines
    lines = remove_duplicate_lines(lines)

    transcript = " ".join(lines)
    transcript = capitalize_first_letter(transcript)

    # Restore punctuation
    transcript = restore_punctuation(transcript)

    # Save the transcript to a file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)

    # Print the full path of the output file
    final_path = Path(output_file).resolve()

    # Delete the original VTT file
    if args.delete:
        os.remove(input_file)

    print(str(final_path))
    return final_path

if __name__ == "__main__":
    final_path = main()
