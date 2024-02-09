#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert a WebVTT subtitle file to a formatted-ish transcript.
Useful for summarization and other NLP tasks.

Usage:
    python3 vtt_to_transcript.py <video_url or vtt_file>
"""

import argparse
import html
import logging
import os
import re
import sys
import contextlib
from pathlib import Path
from yaspin import yaspin

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
    with open(os.devnull, "w", encoding="utf-8") as devnull:
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
    subtitle_formats = ["en", "en-US", "en-en"]

    with yaspin(text="Downloading VTT file...", color="yellow") as sp:
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

                if not available_subtitles:
                    logging.error("No subtitles available.")
                    return None

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


def format_transcript(text: str) -> str:
    """
    Format the transcript text by fixing HTML entities and normalizing spaces.
    """
    # Unescape HTML entities
    text = html.unescape(text)

    # Normalize spaces (replace multiple spaces with a single space)
    text = re.sub(r"\s+", " ", text)

    # Trim spaces before punctuation (optional, based on preference)
    text = re.sub(r"\s+([,.])", r"\1", text)

    return text


def restore_punctuation(text: str) -> str:
    """
    Restore punctuation to a string/transcript
    """
    from deepmultilingualpunctuation import PunctuationModel

    model = PunctuationModel()
    return model.restore_punctuation(text)


def insert_paragraph_breaks(text: str, sentences_per_paragraph: int = 4) -> str:
    """
    Insert paragraph breaks into the text after a specified number of sentences.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    paragraphs = []
    paragraph = []

    for sentence in sentences:
        paragraph.append(sentence)
        if len(paragraph) >= sentences_per_paragraph:
            paragraphs.append(" ".join(paragraph))
            paragraph = []
    # Add any remaining sentences as a final paragraph
    if paragraph:
        paragraphs.append(" ".join(paragraph))

    return "\n\n".join(paragraphs)


def main():
    """
    Downloading the VTT, processing the transcript, and saving the output.
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

    # Check if input is None
    if input_file is None:
        logging.error("Failed to download or otherwise find the VTT file.")
        sys.exit(1)

    output_title = input_file.split(".")[0]
    output_file = f"{output_title}_formatted.txt"

    with yaspin(text="Processing transcript...", color="green") as sp:
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

        # Format the transcript
        transcript = format_transcript(transcript)

        # Insert paragraph breaks
        transcript = insert_paragraph_breaks(transcript, sentences_per_paragraph=4)

        # Save the transcript to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)

        # Print the full path of the output file
        final_path = Path(output_file).resolve()

        # Delete the original VTT file if requested
        if args.delete:
            os.remove(input_file)

        print(str(final_path))
        return final_path


if __name__ == "__main__":
    main()
