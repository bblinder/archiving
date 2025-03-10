#!/usr/bin/env python3

"""Downloads YouTube Videos and converts them via FFmpeg into mp3s."""

import os
import shutil
import sys

from rich.console import Console
from rich.prompt import Prompt

# Create console without showing traceback paths
console = Console(highlight=False)
prompt = Prompt()

try:
    from yt_dlp import YoutubeDL
except ImportError:
    console.print("::: YouTube-DLP not found.")
    console.print("::: Please ensure it's installed.")
    sys.exit(1)


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
        console.print("FFmpeg not found.", style="bold red")
        console.print("Please ensure it's installed.", style="bold red")
        sys.exit(1)


class MyLogger(object):
    """Logger for yt-dlp."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        console.print(f"Warning: {msg}", style="yellow")

    def error(self, msg):
        console.print(f"Error: {msg}", style="bold red")


def progress_hook(d):
    """Display progress information."""
    if d["status"] == "downloading":
        if "total_bytes" in d and d["total_bytes"] > 0:
            percent = d["downloaded_bytes"] / d["total_bytes"] * 100
            print(f"Downloaded {percent:.1f}%", end="\r")
        elif "total_bytes_estimate" in d and d["total_bytes_estimate"] > 0:
            percent = d["downloaded_bytes"] / d["total_bytes_estimate"] * 100
            print(f"Downloaded {percent:.1f}% (est)", end="\r")
    elif d["status"] == "finished":
        console.print("Download finished, now converting...", style="green")


def get_video_info(url):
    """Get video information without downloading."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def file_exists(title, output_dir):
    """Check if a file with the given title already exists in the output directory."""
    # Clean the title to create a filename-safe string
    safe_title = "".join(c for c in title if c.isalnum() or c in " ._-").strip()
    possible_filenames = [f"{safe_title}.mp3", f"{title}.mp3"]

    for filename in possible_filenames:
        if os.path.exists(os.path.join(output_dir, filename)):
            return True, filename

    return False, None


def download_url(url, args):
    """
    Download the video as an mp3, and retain thumbnail and metadata.
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(args.output):
            os.makedirs(args.output)
            console.print(f"Created output directory: {args.output}", style="blue")

        # Check if file already exists
        info = get_video_info(url)
        title = info.get("title", "Unknown Title")
        exists, existing_file = file_exists(title, args.output)

        if exists and not args.force:
            console.print(
                f"File '{existing_file}' already exists in the output directory.",
                style="yellow",
            )
            overwrite = prompt.ask("Do you want to overwrite? (y/n)", default="n")
            if overwrite.lower() != "y":
                console.print("Download skipped.", style="yellow")
                return True, existing_file

        output_path = os.path.join(args.output, "%(title)s.%(ext)s")

        # Determine quality based on args
        quality = "128" if args.low_quality else "320"
        console.print(f"Using audio quality: {quality}kbps", style="blue")

        ydl_opts = {
            "outtmpl": output_path,
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
                    "preferredquality": quality,
                },
                {
                    "key": "EmbedThumbnail",
                },
            ],
            "logger": MyLogger(),
            "progress_hooks": [progress_hook],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url)

        # Get the filename that was actually created
        filename = f"{title}.mp3"
        return True, filename
    except KeyboardInterrupt:
        console.print("\nDownload cancelled by user.", style="yellow")
        raise
    except Exception as e:
        console.print(f"Download failed: {str(e)}", style="bold red")
        return False, None


def is_valid_url(url):
    """Basic URL validation."""
    return url and (url.startswith("http://") or url.startswith("https://"))


def main():
    import argparse

    argparser = argparse.ArgumentParser(description="Download YouTube videos as MP3s")
    argparser.add_argument(
        "-o",
        "--output",
        help="The directory to download to",
        default=get_downloads_folder(),
        required=False,
    )
    argparser.add_argument(
        "-l",
        "--low-quality",
        help="Use lower quality (128kbps) instead of high quality (320kbps)",
        action="store_true",
    )
    argparser.add_argument(
        "-f",
        "--force",
        help="Force download even if file already exists",
        action="store_true",
    )
    argparser.add_argument(
        "urls",
        nargs="*",
        help="URLs to download (optional, can be entered interactively)",
    )
    args = argparser.parse_args()

    ffmpeg_check()  # Check if FFmpeg is installed.

    # Get URLs from command line or prompt
    urls_to_download = args.urls
    if not urls_to_download:
        try:
            url = prompt.ask("Enter URL").strip()
            if not is_valid_url(url):
                console.print("Invalid URL provided.", style="bold red")
                sys.exit(1)
            urls_to_download = [url]
        except KeyboardInterrupt:
            console.print("\nOperation cancelled by user.", style="yellow")
            sys.exit(0)

    try:
        # Process each URL
        for url in urls_to_download:
            if not is_valid_url(url):
                console.print(f"Skipping invalid URL: {url}", style="yellow")
                continue

            console.print(f"Processing: {url}", style="blue")
            console.print("Downloading and converting to MP3...", style="blue")

            success, filename = download_url(url, args)

            if success:
                if filename:
                    console.print(
                        f"Successfully downloaded {url} to {os.path.join(args.output, filename)}",
                        style="bold green",
                    )
                else:
                    console.print(f"Successfully processed {url}", style="bold green")
            else:
                console.print(f"Failed to download {url}", style="bold red")
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user. Exiting...", style="yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
