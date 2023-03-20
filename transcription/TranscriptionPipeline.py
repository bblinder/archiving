#!/usr/bin/env python3

"""
Downloads a YouTube video as an mp3 file and transcribes its audio using OpenAI's whisper model. 

Functions:
- download_video(url: str) -> str: Downloads a YouTube video as an mp3 file 
and returns the path to the audio file.

- transcribe_audio(audio_file: str) -> None: Transcribes the audio file using OpenAI's whisper model
and outputs the text to a file.

Requirements:
- Python 3.6 or higher
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

try:
    import whisper
except ImportError:
    print("whisper not installed.")
from halo import Halo
from rich.console import Console
from rich.prompt import Prompt

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("yt-dlp not installed.")

console = Console()
prompt = Prompt()


logger = console.log


def download_video(url):
    """
    Download the video at 128kbps as an mp3, and retain thumbnail and metadata.
    """
    output_path = os.path.join(os.getcwd(), "%(title)s.%(ext)s")
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
                "preferredquality": "128",
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
        "logger": logger,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url)

    return os.path.join(
        os.getcwd(),
        output_path
        % {"title": ydl.extract_info(url, download=False).get("title"), "ext": "mp3"},
    )


def transcribe_audio(audio_file):
    """
    Transcribe the audio file using OpenAI's whisper and output to a text file.
    """
    model = whisper.load_model("medium.en")
    audio = whisper.load_audio(audio_file)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)
    transcribed_text = result.text

    with open(
        f"{os.path.splitext(audio_file)[0]}.txt", "w", encoding="utf-8"
    ) as text_file:
        text_file.write(transcribed_text)


if __name__ == "__main__":
    URL = prompt.ask("Enter the YouTube video URL: ")
    spinner = Halo(text="Downloading video...", spinner="dots")
    spinner.start()
    audio_file = download_video(URL)
    spinner.succeed("Video downloaded!")
    spinner.end()
    transcribe_audio(audio_file)
