#!/usr/bin/env python3

""" A script to convert a video downloaded with yt-dlp to an audio format using ffmpeg."""

import argparse
import os
import subprocess
import sys
from shutil import which

# Define supported audio formats
SUPPORTED_FORMATS = [".m4a", ".webm", ".opus", ".mkv", ".ogg", ".wav", ".flac"]


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Convert audio files to mp3")
    parser.add_argument("audio_file", help="audio file to convert")
    return parser.parse_args()


def check_ffmpeg_installed():
    """Check if ffmpeg is installed."""
    if not which("ffmpeg"):
        print("Error: ffmpeg is not installed.", file=sys.stderr)
        sys.exit(1)


def convert_to_mp3(audio_file):
    """Convert an audio file to MP3 format."""
    if not os.path.isfile(audio_file):
        print("Error: File does not exist.", file=sys.stderr)
        sys.exit(1)

    file_name, file_ext = os.path.splitext(audio_file)
    if file_ext.lower() == ".mp3":
        print("File is already in mp3 format. Exiting...")
        return

    if file_ext.lower() in SUPPORTED_FORMATS:
        new_file = f"{file_name}.mp3"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    audio_file,
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "320k",
                    new_file,
                ],
                check=True,
            )
            print(f"Conversion successful: {new_file}")
            os.remove(audio_file)
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("File format not supported for conversion. Supported formats are:")
        for fmt in SUPPORTED_FORMATS:
            print(f"* {fmt}")
        sys.exit(1)


def main():
    args = parse_arguments()
    check_ffmpeg_installed()
    convert_to_mp3(args.audio_file)


if __name__ == "__main__":
    main()
