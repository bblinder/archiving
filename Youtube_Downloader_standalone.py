#!/usr/bin/env python3

# Downloads YouTube Videos and converts them via FFmpeg into mp3s.

from __future__ import unicode_literals
from halo import Halo
import os
import sys
from shutil import which
import simple_colors as sc


try:
    from yt_dlp import YoutubeDL
except ImportError:
    print(sc.red("::: YouTube-DLP not found."))
    print(sc.red("::: Please ensure it's installed."))
    sys.exit(1)


if not which('ffmpeg'):
    print(sc.red("::: FFmpeg not found."))
    print(sc.red("::: Please ensure it's installed."))


def get_music_folder():
    if os.name == 'nt':
        return os.path.join(os.environ['USERPROFILE'], 'Music')
    else:
        return os.path.join(os.path.expanduser('~'), 'Music')


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


@Halo(text='Downloading and converting...', spinner='dots')
def download_url(url):
    ydl_opts = {
        'outtmpl': get_music_folder() + '/' + '%(title)s.%(ext)s',
        'writethumbnail': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }, 
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        },
        {
            'key': 'EmbedThumbnail',
        }],
        'logger': MyLogger()
        # 'progress_hooks': [my_hook],
    }

    with YoutubeDL(ydl_opts) as ydl:
        """ Download video and store its name in a variable """
        title = ydl.extract_info(url, download=True)['title']
    return title


if __name__ == '__main__':
    url = input("Enter URL: ").strip()  # Asking for URL and sanitizing it.
    download_url(url)
    if download_url(url):
        print("Successfully downloaded " + sc.green(str(download_url(url)), 'bold') + " to Music folder.")
