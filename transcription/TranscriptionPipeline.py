#!/usr/bin/env python3

import os

import whisper
from rich.console import Console
from rich.prompt import Prompt
from yt_dlp import YoutubeDL

console = Console()
prompt = Prompt()


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        console.log(msg)


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
        "logger": MyLogger(),
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
    audio_file = download_video(URL)
    transcribe_audio(audio_file)
