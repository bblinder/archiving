#!/usr/bin/env python3

# Downloads YouTube Videos and converts them via FFmpeg into mp3s.

from __future__ import unicode_literals

import shutil
import sys

from halo import Halo

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("::: YouTube-DLP not found. \n::: Install it with 'pip install yt_dlp'")


def ffmpeg_check():
    """Check if FFmpeg is installed."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("::: FFmpeg not found in $PATH.")
        print("::: Please ensure it's installed.")
        sys.exit(1)


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


ydl_opts = {
    "outtmpl": "%(title)s.%(ext)s",
    "writethumbnail": True,
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegMetadata",
            "add_metadata": True,
        },
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        },
        {"key": "EmbedThumbnail"},
    ],
    "logger": MyLogger(),
}


@Halo(text="Downloading and converting... ", spinner="dots")
def download_url(url):
    with YoutubeDL(ydl_opts) as ydl:
        title = ydl.extract_info(url, download=True)["title"]
        print("\n\nDownloaded and converted: " + title)
    return title


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Downloads YouTube Videos and converts them via FFmpeg into mp3s."
    )
    parser.add_argument("URL", help="The URL of the track to download")
    args = parser.parse_args()
    url = args.URL.strip()

    ffmpeg_check()

    download = lambda: True if download_url(url) else print("::: Something went wrong.")
    download()
