#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description="Convert audio files to mp3")
parser.add_argument("audio_file", help="audio file to convert")
args = parser.parse_args()

# Checking if ffmpeg is installed
try:
    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, check=True)
except FileNotFoundError:
    print("ffmpeg is not installed")
    sys.exit(1)


formats = [".m4a", ".webm", ".opus", ".mkv", ".ogg", ".wav", ".flac"]
file_path = os.path.dirname(args.audio_file)


def mp3_convert(audio_file):
    """Convert file to mp3. If file is already mp3, do nothing"""

    if not os.path.isfile(audio_file):
        print("::: File not specified.")
        sys.exit(1)

    if audio_file.endswith(".mp3"):
        print("::: File is already mp3. Exiting...")
        sys.exit(0)
    else:
        file_name = os.path.splitext(audio_file)[0]
        file_ext = os.path.splitext(audio_file)[1]
        if file_ext in formats:
            new_file = file_name + ".mp3"
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
            os.remove(audio_file)
        else:
            print("\nFile doesn't match any of the supported formats:")
            # print formats as bullet points
            for format in formats:
                print(f"* {format}")
            sys.exit(1)


if __name__ == "__main__":
    mp3_convert(args.audio_file)
