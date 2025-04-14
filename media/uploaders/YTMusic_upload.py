#!/usr/bin/env python3

"""
derived from: https://ytmusicapi.readthedocs.io/
See "Setup" on how to get auth headers.
"""

import argparse
import os
import sys
from functools import partial

try:
    from ytmusicapi import YTMusic
    from halo import Halo
except ImportError as e:
    print(f"::: {e}\n::: Exiting...")
    sys.exit(1)


def setup_argparser():
    """Set up and return command line arguments."""
    parser = argparse.ArgumentParser(
        description="This script uploads a music track or directory of tracks to YouTube Music"
    )
    parser.add_argument("track", help="The path to the track or directory to upload")
    parser.add_argument(
        "-c", "--config", help="The path to the config file", default="headers_auth.json"
    )
    return parser.parse_args()


def init_ytmusic(auth_file):
    """Initialize the YTMusic object."""
    if os.path.isfile(auth_file):
        return YTMusic(auth_file)
    else:
        print(f"::: {auth_file} does not exist...")
        sys.exit(1)


def check_for_upload(track, ytmusic):
    """Check if the track already exists in YT Music library."""
    spinner = Halo(text="Checking for existing upload...", spinner="dots")
    spinner.start()
    track_name = os.path.splitext(os.path.basename(track))[0]
    search_results = ytmusic.search(track_name, scope="uploads")
    spinner.stop()
    if search_results:
        print(f"::: Track already exists on YT Music: {search_results[0]['title']}")
        return True


def convert_bytes(bytes_number):
    """Convert bytes to a human-readable format."""
    tags = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while i < len(tags) and bytes_number >= 1024:
        bytes_number /= 1024
        i += 1
    return f"{round(bytes_number, 2)} {tags[i]}"


def print_filesize(track, filepath):
    """Print the file size of the track in a human-readable format."""
    filesize = os.path.getsize(filepath)
    print(f"{track}: {convert_bytes(filesize)}")


def upload_track(track, ytmusic):
    """Upload a single track to YouTube Music."""
    print_filesize(track, track)
    ytmusic.upload_song(track)


def upload_directory(directory, ytmusic):
    """Upload all tracks in a directory to YouTube Music."""
    music_formats = [".mp3", ".m4a", ".flac", ".wma", ".ogg"]
    for root, _, files in os.walk(directory):
        for track in filter(lambda f: f.endswith(tuple(music_formats)), files):
            filepath = os.path.join(root, track)
            print_filesize(track, filepath)
            ytmusic.upload_song(filepath)


@Halo(text="Uploading...", spinner="dots")
def main(track, ytmusic):
    """Upload a track or all tracks in a directory to YouTube Music."""
    if os.path.isfile(track):
        upload_track(track, ytmusic)
    elif os.path.isdir(track):
        upload_directory(track, ytmusic)
    else:
        print("No track or music folder specified")
        sys.exit(1)


if __name__ == "__main__":
    args = setup_argparser()
    ytmusic = init_ytmusic(args.config)
    check_upload = partial(check_for_upload, args.track, ytmusic)

    if check_upload():
        answer = input("::: Do you want to upload anyway? [y/N] ")
        if answer.lower() == "y":
            main(args.track, ytmusic)
    else:
        main(args.track, ytmusic)
