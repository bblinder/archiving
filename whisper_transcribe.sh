#!/usr/bin/env bash

# This script transcribes audio files using the whisper library
# Requires: whisper, ffmpeg
# Usage: ./whisper_transcribe.sh [audio file] [text format]

set -euo pipefail
set +u


AUDIO_FILE="$1"
TEXT_FORMAT="$2"


check_dependencies() {
    if ! command -v whisper &> /dev/null ; then
    echo "whisper could not be found"
    exit 1
    fi
}


validate_input() {
    # if no input file is provided
    if [[ -z "$AUDIO_FILE" ]]; then
    echo "No audio file provided"
    exit 1
    fi
}

transcribe() {
    whisper --model medium.en "$AUDIO_FILE" -f "$TEXT_FORMAT" --transcribe
}


display_help() { 
    echo "Usage: $0 [audio file] [text format]"
    echo ""
    echo "Arguments:"
    echo "  audio file: path to audio file"
    echo "  text format: text format to output (example: 'txt' or 'json')"
}

if [[ "$#" -eq 0 ]]; then
    display_help
    exit 1
fi

check_dependencies
validate_input
transcribe