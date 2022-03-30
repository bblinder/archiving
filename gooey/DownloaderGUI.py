#!/usr/bin/env python3

from __future__ import unicode_literals
from gooey import Gooey, GooeyParser
import os, sys
from fbs_runtime.application_context.PyQt6 import ApplicationContext
from PyQt6.QtWidgets import QMainWindow

try:
	from yt_dlp import YoutubeDL
except ImportError:
	print("::: YouTube-DLP not found. \n::: Install it with 'pip install yt_dlp'")

def get_downloads_folder():
    if os.name == 'nt':
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    else:
        return os.path.join(os.path.expanduser('~'), 'Downloads')

class MyLogger(object):
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		print(msg)

ydl_opts = {
	'outtmpl': get_downloads_folder() + '/' + '%(title)s.%(ext)s',
	'writethumbnail': False,
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegMetadata',
		'add_metadata': True,
	}, 
	{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '320',
		}],
	'logger': MyLogger()
}

def download_url(url):
	with YoutubeDL(ydl_opts) as ydl:
		# Print progress
		print("Downloading and Converting... please wait...")
		title = ydl.extract_info(url, download=True)['title']
	return title

@Gooey(
	program_name="Youtube --> MP3",
	program_description="Downloads Youtube videos and converts them to high fidelity mp3 files.",
	#progress_regex=r"^Progress (\d+)$",
)

def main():
	parser = GooeyParser()
	downloader = parser.add_argument_group("Download Options")
	downloader.add_argument("URL", help="The URL of the track to download",
		widget="TextField",
		metavar="URL",
		gooey_options={
			'validator': {
				'test': 'user_input.startswith("http")',
				'message': 'Please enter a valid URL'
			}
		})
	args = parser.parse_args()
	download_url(args.URL)
	args = parser.parse_args()
	download_url(args.URL)
	args = parser.parse_args()
	url = args.URL.strip()

	download_url(url)
	if download_url(url):
		print("\nSuccessfully downloaded " + str(download_url(url)) + " to " + get_downloads_folder())

if __name__ == '__main__':
	appctxt = ApplicationContext() # 1. Instantiate ApplicationContext
	window = QMainWindow()
	window.resize(250, 150)
	window.show()
	main()
	exit_code = appctxt.app.exec() # 2. Invoke appctxt.app.exec()
	sys.exit(exit_code)
