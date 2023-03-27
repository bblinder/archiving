#!/usr/bin/env bash

# This script transcribes audio files using the Whisper library
# Requires: Whisper, FFmpeg
# Usage: ./whisper_transcribe.sh [audio file] [text format]

set -euo pipefail

display_help() {
    echo "Usage: $0 [audio file] [text format]"
    echo ""
    echo "Arguments:"
    echo "  audio file: path to audio file"
    echo "  text format: text format to output (example: 'txt', 'json', 'srt', 'all')"
}

check_dependencies() {
    if ! command -v whisper &> /dev/null ; then
        echo "::: Whisper could not be found"
        exit 1
    fi

    if ! command -v ffmpeg &> /dev/null ; then
        echo "::: FFmpeg could not be found"
        exit 1
    fi
}

validate_input() {
    # if no input file is provided
    if [[ -z "$AUDIO_FILE" ]]; then
        echo "::: No audio file provided"
        exit 1
    fi

    # check if the input file exists
    if [[ ! -f "$AUDIO_FILE" ]]; then
        echo "::: Input file does not exist"
        exit 1
    fi
}

transcribe() {
    whisper --model medium.en "$AUDIO_FILE" -f "$TEXT_FORMAT" --task transcribe
}

if [[ "$#" -eq 0 ]]; then
    display_help
    exit 1
fi

# get arguments
AUDIO_FILE="$1"
TEXT_FORMAT="$2"

check_dependencies
validate_input
transcribe
