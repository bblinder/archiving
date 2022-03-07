#!/usr/bin/env python3

# Downloads YouTube Videos and converts them via FFmpeg into mp3s.

from __future__ import unicode_literals

try:
	from yt_dlp import YoutubeDL
except ImportError:
	print("::: YouTube-DLP not found.")
	print("::: Please ensure it's installed.")

#YT_URL = sys.argv[1]
class MyLogger(object):
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		print(msg)

def my_hook(d):
	if d['status'] == 'finished':
		print('::: Done downloading, now converting...')

ydl_opts = {
	'writethumbnail': True,
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '320',
		}],
	'logger': MyLogger(),
	'progress_hooks': [my_hook],
}

def download_url(url):
	with YoutubeDL(ydl_opts) as ydl:
		ydl.download([url])

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description="Downloads YouTube Videos and converts them via FFmpeg into mp3s.")
	parser.add_argument("URL", help="The URL of the track to download")
	args = parser.parse_args()
	url = args.URL

	download_url(url)
