#!/usr/bin/env bash

set -euo pipefail
shopt -s nullglob
shopt -s nocaseglob
trap cleanup SIGINT SIGTERM ERR EXIT

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
  # script cleanup here
}

setup_colors() {
  if [[ -t 2 ]] && [[ -z "${NO_COLOR-}" ]] && [[ "${TERM-}" != "dumb" ]]; then
    NOFORMAT='\033[0m' RED='\033[0;31m' GREEN='\033[0;32m' ORANGE='\033[0;33m' BLUE='\033[0;34m' PURPLE='\033[0;35m' CYAN='\033[0;36m' YELLOW='\033[1;33m'
  else
    NOFORMAT='' RED='' GREEN='' ORANGE='' BLUE='' PURPLE='' CYAN='' YELLOW=''
  fi
}

msg() {
  echo >&2 -e "${1-}"
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "$msg"
  exit "$code"
}


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

setup_colors

YT_DL "$@"
mp3_convert
remove_originals

shopt -u nullglob
shopt -u nocaseglob
