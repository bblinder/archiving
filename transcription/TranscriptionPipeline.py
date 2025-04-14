#!/usr/bin/env python3

"""
Downloads a YouTube video as an mp3 file and transcribes its audio using OpenAI's whisper model. 

Functions:
- download_video(url: str) -> str: Downloads a YouTube video as an mp3 file 
and returns the path to the audio file.

- transcribe_audio(audio_file: str) -> None: Locally transcribes the audio file using OpenAI's whisper model
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
from shutil import which

import whisper
from rich.console import Console
from rich.prompt import Prompt
from yt_dlp import YoutubeDL
from halo import Halo

console = Console()
prompt = Prompt()


def ffmpeg_check():
    """
    Check if ffmpeg is installed.
    """
    if which("ffmpeg") is None:
        raise FileNotFoundError("ffmpeg not installed.")


def check_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        raise ImportError(f"{module_name} not installed.")


def download_video(url, output_dir):
    """
    Download the video at 48kbps as an mp3, and retain thumbnail and metadata.
    """

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "%(title)s.%(ext)s")
    info = YoutubeDL().extract_info(url, download=False)
    title = info["title"]
    path_to_file = os.path.join(output_dir, f"{title}.mp3")
    if os.path.isfile(path_to_file):
        console.print(
            f"[bold red]{title} already downloaded. Skipping this part...[/bold red]"
        )
        return path_to_file

    ydl_opts = {
        "outtmpl": output_path,
        "writethumbnail": True,
        "format": "wav/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "16",
            },
            #{
            #    "key": "EmbedThumbnail",
            #},
        ],
        # "logger": logger,
    }

    with YoutubeDL(ydl_opts) as ydl:
        path_to_file = os.path.join(
            output_dir, ydl.extract_info(url, download=True)["title"] + ".wav"
        )

    return path_to_file


def transcribe_audio(audio_file, output_path):
    model = whisper.load_model("medium.en")
    #model = whisper.load_model("small.en")
    result = model.transcribe(audio_file, fp16=False)

    with open(output_path, "w") as f:
        f.write(result["text"])

    console.print(
        f"[bold green]Transcription complete. Output saved to {output_path}[/bold green]"
    )


if __name__ == "__main__":
    check_module("whisper")
    check_module("yt_dlp")
    check_module("rich")
    ffmpeg_check()

    url = prompt.ask("Enter the YouTube video URL")
    output_dir = os.path.join(os.getcwd(), "transcriptions")
    audio_file = download_video(url, output_dir)

    output_path = os.path.splitext(audio_file)[0] + ".txt"

    spinner = Halo(
        text="\nTranscribing audio... please be patient, this might take a while...",
        spinner="dots",
    )
    spinner.start()
    transcribe_audio(audio_file, output_path)
    spinner.stop()
