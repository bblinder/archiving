#!/usr/bin/env python3

"""Downloads YouTube Videos and converts them via FFmpeg into mp3s."""

from __future__ import unicode_literals

import os
import shutil
import sys

import simple_colors as sc
from halo import Halo

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("::: YouTube-DLP not found.")
    print("::: Please ensure it's installed.")


def get_downloads_folder():
    """Get the user's Downloads folder. Windows vs. Mac/Linux."""
    if os.name == "nt":
        downloads_folder = os.path.join(os.environ["USERPROFILE"], "Downloads")
    else:
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    return downloads_folder


def ffmpeg_check():
    """Check if FFmpeg is installed."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("::: FFmpeg not found.")
        print("::: Please ensure it's installed.")
        sys.exit(1)


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


@Halo(text="Downloading and converting to MP3...", spinner="dots")
def download_url(url):
    """
    Download the video at 320kbps as an mp3, and retain thumbnail and metadata.
    """
    ydl_opts = {
        "outtmpl": args.output + "/" + "%(title)s.%(ext)s",
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
            {
                "key": "EmbedThumbnail",
            },
        ],
        "logger": MyLogger()
        # 'progress_hooks': [my_hook],
    }

    with YoutubeDL(ydl_opts) as ydl:
        # Download video and store its name in a variable
        title = ydl.extract_info(url, download=True)["title"]
    return title


if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-o",
        "--output",
        help="The directory to download to",
        default=get_downloads_folder(),
        required=False,
    )
    args = argparser.parse_args()

    ffmpeg_check()  # Check if FFmpeg is installed.

    url = input("Enter URL: ").strip()  # Asking for URL and sanitizing it.
    if not url:
        print("::: No URL provided.")
        sys.exit(1)

    download_folder = args.output if args.output else get_downloads_folder()
    download_url(url)
    if download_url(url):
        print(
            f"Successfully downloaded {sc.green(str(download_url(url)), 'bold')} to {download_folder}.\n"
        )
