#!/usr/bin/env python3

"""
derived from: https://ytmusicapi.readthedocs.io/
See "Setup" on how to get auth headers.
"""

import argparse
import os
import sys

try:
    from ytmusicapi import YTMusic
except ImportError:
    print("::: Can't import ytmusicapi - check that it's installed")
    print("::: Exiting...")
    sys.exit(1)

try:
    from halo import Halo
except ImportError:
    print("::: Halo not installed - please install with: ")
    print("::: 'pip install halo' ")
    print("::: Exiting... ")
    sys.exit(1)

parser = argparse.ArgumentParser(
    description="This script uploads a music track or directory of tracks to YouTube Music"
)
parser.add_argument("track", help="The path to the track or directory to upload")
parser.add_argument(
    "-c", "--config", help="The path to the config file", default="headers_auth.json"
)
args = parser.parse_args()

# https://ytmusicapi.readthedocs.io/en/latest/setup.html#using-the-headers-in-your-project
authFile = args.config  # You need to create this ahead of time.

if os.path.isfile(authFile):
    ytmusic = YTMusic(authFile)
else:
    print(f"::: {authFile} does not exist...")
    sys.exit(1)


def check_for_upload(track):
    """Check if the track already exists in YT Music library"""
    spinner = Halo(text="Checking for existing upload...", spinner="dots")
    spinner.start()
    track_name = os.path.splitext(os.path.basename(track))[0]
    search_results = ytmusic.search(track_name, scope="uploads")
    spinner.stop()
    if search_results:
        print(f"::: Track already exists on YT Music: {search_results[0]['title']}")
        return True


def convert_bytes(bytes_number):
    """Display file size to something readable"""

    tags = ["Bytes", "KB", "MB", "GB", "TB"]

    i = 0
    double_bytes = bytes_number

    while i < len(tags) and bytes_number >= 1024:
        double_bytes = bytes_number / 1024.0
        i += 1
        bytes_number = bytes_number / 1024

    return str(round(double_bytes, 2)) + " " + tags[i]


@Halo(text="Uploading...", spinner="dots")
def main(track):
    """
    Determines if the track is a file or directory and uploads accordingly.
    """

    music_formats = [".mp3", ".m4a", ".flac", ".wma", ".ogg"]
    if os.path.isfile(track):
        filesize = os.path.getsize(track)
        print(f"{track}: {convert_bytes(filesize)}")
        ytmusic.upload_song(track)
    elif os.path.isdir(track):
        for root, dirs, files in os.walk(track):
            # ignore jpgs and other non-audio files
            for track in files:
                if track.endswith(tuple(music_formats)):
                    filesize = os.path.getsize(os.path.join(root, track))
                    print(f"{track}: {convert_bytes(filesize)}")
                    ytmusic.upload_song(os.path.join(root, track))
    else:
        print("No track or music folder specificed")
        sys.exit(1)


if __name__ == "__main__":
    if check_for_upload(args.track):
        answer = input("::: Do you want to upload anyway? [y/N] ")
        if answer.lower() == "y":
            main(args.track)
        else:
            pass
    else:
        main(args.track)
