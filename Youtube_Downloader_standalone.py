#!/usr/bin/env python3

"""Downloads YouTube Videos and converts them via FFmpeg into mp3s."""

from __future__ import unicode_literals

import os
import shutil
import sys

from halo import Halo
from rich.console import Console
from rich.prompt import Prompt

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("::: YouTube-DLP not found.")
    print("::: Please ensure it's installed.")

console = Console()
prompt = Prompt()


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
        console.log("FFmpeg not found.", style="bold red")
        console.log("Please ensure it's installed.", style="bold red")
        sys.exit(1)


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


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
        "logger": MyLogger(),
    }

    with YoutubeDL(ydl_opts) as ydl:
        title = ydl.extract_info(url)["title"]

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

    url = prompt.ask("Enter URL").strip()  # Asking for URL and sanitizing it.
    if not url:
        console.log("No URL provided.", style="bold red")
        sys.exit(1)

    spinner = Halo(text="Downloading and converting to MP3...", spinner="dots")
    spinner.start()
    download_url(url)
    spinner.stop()

    console.log(f"Successfully downloaded {url} to {args.output}.", style="bold green")
