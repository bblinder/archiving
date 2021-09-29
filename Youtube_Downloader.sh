#!/usr/bin/env bash

set -euo pipefail
shopt -s nullglob
shopt -s nocaseglob

mp3_convert() {
	for fname in ./*.{m4a,webm,opus,ogg,mp3}; do
		ffmpeg -i "$fname" -c:a libmp3lame -b:a 320k "${fname%.*}.mp3"
	done
}

if [[ ! "$(command -v ffmpeg)" ]]; then
	echo -e "::: ffmpeg not found. Please make sure it's installed.\\n"
	exit 1
fi

if [[ ! "$(command -v yt-dlp)" ]]; then
	echo -e "::: Youtube-dlp not found in your PATH"
	echo -e "::: Please make sure it's installed.\\n"
	exit 1
fi

YT_DL() {
	if [[ "$#" -eq 0 ]]; then
		echo -e "::: No URL provided"
		echo -e "\\n::: Usage: ./Youtube_Downloader.sh [URL]"
		exit 1
	else
		yt-dlp --add-metadata --extract-audio --output "%(uploader)s - %(upload_date)s - %(title)s [%(id)s].%(ext)s" --extractor-args youtube:player_client=android "$1"
	fi
}

remove_originals() {
	read -rp "::: Delete the originals [y/n]? -->  " delete_response
	case "$delete_response" in
	[yY])
		echo -e "\\n::: Deleting..."
		sleep 0.5
		rm ./*.{m4a,webm,opus,ogg}
		sleep 0.5
		;;
	*)
		exit
		;;
	esac
}

YT_DL "$@"
mp3_convert
remove_originals

shopt -u nullglob
shopt -u nocaseglob
