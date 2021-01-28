#!/usr/bin/env python3

# Downloads YouTube Videos and converts them via FFmpeg into mp3s.

from __future__ import unicode_literals
import sys
try:
	import youtube_dl
except ImportError:
	print("Youtube_dl not found.")
	print("Please ensure it's installed.")

YT_URL = sys.argv[1]
class MyLogger(object):
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		print(msg)

def my_hook(d):
	if d['status'] == 'finished':
		print('Done downloading, now converting...')

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

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	ydl.download([YT_URL])
