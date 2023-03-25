#!/usr/bin/env python3

"""
Downloads a video from YouTube, converts it to mp3
If it's bigger than 25MB, splits it into 10MB segments.
Transcribes it using OpenAI's Whisper API.
"""

import json
import logging
import math
import os
import sys
from argparse import ArgumentParser

import openai
import yaml
from pydub import AudioSegment
from tqdm import tqdm
from yt_dlp import YoutubeDL

if not os.path.isfile("config.yaml"):
    raise FileNotFoundError(
        "config.yaml not found. Please create a config.yaml file in the same directory as the script."
    )

with open("config.yaml", "r") as ymlfile:
    config = yaml.safe_load(ymlfile)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def download_video(url, output_dir):
    """
    Download the video at 48kbps as a mp3, and retain thumbnail and metadata.
    """

    os.makedirs(output_dir, exist_ok=True)

    info = YoutubeDL().extract_info(url, download=False)
    title = info["title"]
    path_to_file = os.path.join(output_dir, f"{title}.mp3").strip()
    if os.path.isfile(path_to_file):
        logger.info(f"{title} already downloaded. Skipping this part...")
        return path_to_file

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "writethumbnail": True,
        "format": "mp3/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "48",
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return path_to_file


def split_audio(path_to_file, output_dir):
    """
    Split the audio into 10 minute segments.
    """
    os.makedirs(output_dir, exist_ok=True)
    title = os.path.splitext(os.path.basename(path_to_file))[0]
    audio = AudioSegment.from_file(path_to_file, "mp3")
    duration = len(audio)

    chunk_size = 10 * 60 * 1000
    num_chunks = math.ceil(duration / chunk_size)
    logger.info(f"Splitting {title} into {num_chunks} segments.")

    for i in tqdm(range(num_chunks)):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        segment = audio[start:end]
        segment.export(f"{title.split('.')[0]}_prepared_{i}.mp3", format="mp3")

    # move the chunks into a new directory
    os.makedirs(os.path.join(output_dir, title), exist_ok=True)
    for i in range(num_chunks):
        os.rename(
            f"{title.split('.')[0]}_prepared_{i}.mp3",
            os.path.join(output_dir, title, f"{title}_prepared_{i}.mp3"),
        )

    # return the path to the first chunk
    return os.path.join(output_dir, title, f"{title}_prepared_0.mp3")


def transcribe_audio(path_to_file, output_dir):
    openai.api_key = config["openai_api_key"]
    os.makedirs(output_dir, exist_ok=True)
    title = os.path.splitext(os.path.basename(path_to_file))[0]
    logger.info(f"Transcribing {title}...")

    params = {
        "model": "whisper-1",
        "response_format": "json",
        "prompt": "Hello, please use the transcript of the previous segment if it exists.",
    }

    def transcribe_single_file(path_to_file, params):
        """Transcribe a single file."""

        with open(path_to_file, "rb") as file:
            transcript = openai.Audio.transcribe(file=file, **params)
        if not transcript:
            raise ValueError("Empty transcript received from API")
        return transcript

    # if the file is 25MB or larger, split it into 10MB segments
    if os.path.getsize(path_to_file) > 25 * 1024 * 1024:
        chunks = []
        chunk_size = 10 * 1024 * 1024
        with open(path_to_file, "rb") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)

        transcripts = []
        for chunk in chunks:
            transcript = transcribe_single_file(chunk, params)
            transcripts.append(transcript)

        return transcripts

    else:
        transcript = transcribe_single_file(path_to_file, params)
        return transcript

    return transcript


def main():
    """Putting it all together."""
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", help="URL of the video to download.")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory to save the output files. Default is current directory.",
        default="transcription",
    )
    parser.add_argument(
        "-f", "--file", help="Path to the file to transcribe.", required=False
    )
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.file:
        path_to_file = args.file
        logger.info(f"Transcribing {path_to_file}")
    else:
        path_to_file = download_video(args.url, args.output_dir)
        logger.info(f"Downloaded {path_to_file}")

    # if the file is 25MB or larger, split it into 10 minute segments
    if os.path.getsize(path_to_file) > 25 * 1024 * 1024:
        path_to_file = split_audio(path_to_file, args.output_dir)
        logger.info(f"Split {path_to_file}")

    transcription = str(transcribe_audio(path_to_file, args.output_dir))

    # extract the text field from the JSON payload
    transcription_text = json.loads(transcription)["text"]

    # write transcription text to file, using the title of the video as the filename
    with open(
        os.path.join(
            args.output_dir,
            f"{os.path.splitext(os.path.basename(path_to_file))[0]}.txt",
        ),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(transcription_text)

    # ask to delete the audio file
    delete_audio = input("Delete audio file? (y/n): ").lower()
    if delete_audio == "y":
        os.remove(path_to_file)
        logger.info(f"Deleted {path_to_file}")

    logger.info("Done!")


if __name__ == "__main__":
    main()
