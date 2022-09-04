#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse

parser = argparse.ArgumentParser(description="Convert audio files to mp3")
parser.add_argument("audio_file", help="audio file to convert")
args = parser.parse_args()

# Checking if ffmpeg is installed
try:
    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL)
except FileNotFoundError:
    print("ffmpeg is not installed")
    sys.exit(1)


formats = [".m4a", ".webm", ".opus", ".mkv", ".ogg", ".wav", ".flac"]
file_path = os.path.dirname(args.audio_file)


def mp3_convert(audio_file):
    if not os.path.isfile(audio_file):
        print("File not specified")
        sys.exit(1)
    else:
        for format in formats:
            if format in audio_file:
                new_file = audio_file.replace(format, ".mp3")
                subprocess.run(["ffmpeg", "-i", audio_file, "-c:a", "libmp3lame", "-b:a", "320k", new_file])
                os.remove(audio_file)
            else:
                print(f"::: No {formats} files found")
                sys.exit()


if __name__ == "__main__":
    mp3_convert(args.audio_file)