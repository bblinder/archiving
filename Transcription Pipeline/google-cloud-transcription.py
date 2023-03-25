#!/usr/bin/env python3

import logging
import os
import sys
from argparse import ArgumentParser
from subprocess import run

import google.auth
import yaml
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage

# from google.cloud import speech, storage
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


GCS_BUCKET = config["gcs_bucket"]

# Authenticate with Google Cloud
credentials, project = google.auth.default()


def download_video(url, output_dir):
    """
    Download the video at 48kbps as a WAV, and retain thumbnail and metadata.
    """

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "%(title)s.%(ext)s")
    info = YoutubeDL().extract_info(url, download=False)
    title = info["title"]
    path_to_file = os.path.join(output_dir, f"{title}.wav")
    if os.path.isfile(path_to_file):
        logger.info(f"{title} already downloaded. Skipping this part...")
        return path_to_file

    ydl_opts = {
        "outtmpl": output_path,
        "writethumbnail": False,
        "format": "wav/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "48",
            },
        ],
    }

    with YoutubeDL(ydl_opts) as ydl:
        path_to_file = os.path.join(
            output_dir, ydl.extract_info(url, download=True)["title"] + ".wav"
        )

    return path_to_file


def upload_to_gcs(audio_file, bucket_name):
    """
    Uploads a local file to a Google Cloud Storage bucket.
    """
    storage_client = storage.Client()
    if bucket_name not in [bucket.name for bucket in storage_client.list_buckets()]:
        bucket = storage_client.create_bucket(bucket_name)
    else:
        bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(os.path.basename(audio_file))

    # check if file already exists in bucket
    if blob.exists():
        logger.info(f"File {audio_file} already exists in bucket {bucket_name}.")
        return f"gs://{bucket_name}/{blob.name}", bucket, bucket_name
    else:
        blob.upload_from_filename(audio_file)
        logger.info(f"File {audio_file} uploaded to gs://{bucket_name}/{blob.name}.")
        return f"gs://{bucket_name}/{blob.name}", bucket, bucket_name


def transcribe_gcs(gcs_uri):
    """
    Transcribe the given audio file asynchronously.
    """
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        audio_channel_count=2,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    logger.info("Waiting for operation to complete...")
    response = operation.result(timeout=5400)
    return response


def empty_gcs_bucket(bucket_name):
    """
    Empties a bucket of files. The bucket must exist and be empty.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    for blob in blobs:
        blob.delete()

    logger.info(f"Bucket {bucket_name} emptied.")


def delete_gcs_bucket(bucket_name):
    """
    Deletes a bucket. The bucket must be empty.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    bucket.delete()

    logger.info(f"Bucket {bucket_name} deleted.")


def ffmpeg_convert_to_wav(audio_file):
    """
    Converts an audio file to WAV format.
    """
    # get the file name and extension
    file_name, file_extension = os.path.splitext(audio_file)
    output_path = os.path.join(os.path.dirname(audio_file), f"{file_name}.wav")
    run(
        [
            "ffmpeg",
            "-i",
            audio_file,
            "-acodec",
            "pcm_s16le",
            "-ac",
            "2",
            "-ar",
            "16000",
            output_path,
        ]
    ,check=True)
    return output_path


def main(args):
    """
    Putting it together: taking the argument, downloading the video and/or converting audio to WAV,
    uploading it to GCS, and transcribing it.
    """
    # if no arguments given, print help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Create a temporary directory to store the video and audio files
    output_dir = os.path.join(os.getcwd(), "tmp")
    if args.file:
        if not args.file.endswith(".wav"):
            # Convert the audio file to Google Cloud-recommended WAV format
            path_to_file = ffmpeg_convert_to_wav(args.file)
            logger.info(f"Converted {args.file} to {path_to_file}")
        else:
            path_to_file = args.file  # use the file provided by the user
            logger.info(f"Using existing file: {path_to_file}")
    else:
        # Download the video from YouTube
        path_to_file = str(download_video(args.url, output_dir))
        logger.info(f"Video downloaded to {path_to_file}")

    # Upload the audio file to Google Cloud Storage
    gcs_uri, bucket, bucket_name = upload_to_gcs(path_to_file, GCS_BUCKET)
    logger.info(f"Audio file uploaded to {gcs_uri}")

    # Transcribe the audio file
    response = transcribe_gcs(gcs_uri)
    logger.info("Transcription complete.")

    # Save the transcription to a text file
    output_file = os.path.join(os.getcwd(), "transcription.txt")
    with open(output_file, "w") as f:
        for result in response.results:
            f.write(result.alternatives[0].transcript)
            f.write("\n")

    logger.info(f"Transcription saved to {output_file}")

    # Delete the audio file from Google Cloud Storage
    deletion_request = input(
        "Do you want to delete the audio file from Google Cloud Storage? [y/n] --> "
    ).lower()
    if deletion_request == "y":
        empty_gcs_bucket(bucket_name)
        # delete_gcs_bucket(bucket_name)
        logger.info("Audio file deleted from Google Cloud Storage.")
    else:
        logger.info("Audio file not deleted from Google Cloud Storage.")

    # Delete the temporary directory
    deletion_request = input(
        "Do you want to delete the temporary directory? [y/n] --> "
    ).lower()
    if deletion_request == "y":
        os.remove(path_to_file)
        os.rmdir(output_dir)
        logger.info("Temporary directory deleted.")
    else:
        logger.info("Temporary directory not deleted.")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Transcribe a YouTube video using Google Cloud Speech-to-Text API."
    )
    # parser.add_argument("url", help="YouTube video URL", nargs="?")
    parser.add_argument(
        "-u", "--url", help="YouTube video URL", required=False, type=str
    )
    parser.add_argument("-f", "--file", help="Path to file", required=False, type=str)
    main(parser.parse_args())
