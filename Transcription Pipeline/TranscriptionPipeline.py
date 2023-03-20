#!/usr/bin/env python3

"""
Downloads a YouTube video as an mp3 file and transcribes its audio using OpenAI's whisper model. 

Functions:
- download_video(url: str) -> str: Downloads a YouTube video as an mp3 file 
and returns the path to the audio file.

- transcribe_audio(audio_file: str) -> None: Transcribes the audio file using OpenAI's whisper model
and outputs the text to a file.

Requirements:
- Python 3.6 - 3.9 (whisper doesn't seem to work with higher versions)
- yt-dlp (pip install yt-dlp)
- whisper (OpenAI)
- rich (pip install rich)

Usage:
- Run the script and enter the YouTube video URL when prompted.

Note:
- The downloaded audio file and transcribed text file are saved in the same directory as the script.
- An internet connection is required to download the YouTube video 
and download the whisper model (if not already downloaded).
"""

import os
import sys
from shutil import which
import ffmpeg

try:
    import whisper
except ImportError:
    raise ImportError("whisper not installed.")

from rich.console import Console
from rich.prompt import Prompt

try:
    from yt_dlp import YoutubeDL
except ImportError:
    raise ImportError("yt-dlp not installed.")


try:
    from rich.console import Console
    from rich.prompt import Prompt
except ImportError:
    raise ImportError("rich not installed.")


console = Console()
prompt = Prompt()


logger = console.log

def check_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        raise ImportError(f"{module_name} not installed.")


def download_video(url, output_dir):
    """
    Download the video at 128kbps as an mp3, and retain thumbnail and metadata.
    """
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    output_path = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_path,
        "writethumbnail": False,
        "format": "mp3/bestaudio/best",
        "postprocessors": [
            # {
            #    "key": "FFmpegMetadata",
            #    "add_metadata": True,
            # },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            },
            # {
            #    "key": "EmbedThumbnail",
            # },
        ],
        # "logger": logger,
    }

    with YoutubeDL(ydl_opts) as ydl:
        path_to_file = os.path.join(
            output_dir, ydl.extract_info(url, download=True)["title"] + ".mp3"
        )

    return path_to_file


def transcribe_audio(audio_file, output_path):
    """
    Transcribe the audio file using OpenAI's whisper and output to a text file.
    """
    model = whisper.load_model("medium.en")
    result = model.transcribe(audio_file)


    with open(output_path, "w") as f:
        f.write(result["text"])


if __name__ == "__main__":
    check_module("whisper")
    check_module("yt_dlp")
    check_module("rich")
    

    url = prompt.ask("Enter the YouTube video URL")
    output_dir = os.path.join(os.getcwd(), "downloads")
    audio_file = download_video(url, output_dir)

    output_path = os.path.join(os.getcwd(), "transcription.txt")
    transcribe_audio(audio_file, output_path)

    