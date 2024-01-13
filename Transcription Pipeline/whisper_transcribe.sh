#!/usr/bin/env bash

# Enhanced script to transcribe audio files using the Whisper library
# Requires: Whisper, FFmpeg
# Usage: ./whisper_transcribe.sh [audio file] [text format] [optional: whisper model]

set -euo pipefail

LOG_FILE="transcribe.log"
VALID_FORMATS=("txt" "json" "srt" "all")
DEFAULT_MODEL="medium.en"

display_help() {
    echo "Transcribes audio files using Whisper."
    echo "Usage: $0 [audio file] [text format] [optional: whisper model]"
    echo ""
    echo "Arguments:"
    echo "  audio file: path to the audio file"
    echo "  text format: output format (txt, json, srt, all)"
    echo "  whisper model: optional, Whisper model to use (e.g., 'tiny', 'base'). Default: $DEFAULT_MODEL"
    echo ""
    echo "Example: $0 sample.mp3 txt"
}

log() {
    echo "$(date): $*" >> "$LOG_FILE"
}

check_dependencies() {
    if ! command -v whisper &> /dev/null ; then
        log "::: Whisper could not be found"
        exit 1
    fi

    if ! command -v ffmpeg &> /dev/null ; then
        log "::: FFmpeg could not be found"
        exit 1
    fi
}

validate_input() {
    if [[ -z "$AUDIO_FILE" ]]; then
        log "::: No audio file provided"
        exit 1
    fi

    if [[ ! -f "$AUDIO_FILE" ]]; then
        log "::: Input file does not exist"
        exit 1
    fi

    if [[ ! " ${VALID_FORMATS[*]} " =~ " ${TEXT_FORMAT} " ]]; then
        log "::: Invalid text format provided"
        exit 1
    fi
}

transcribe() {
    if ! whisper --model "$MODEL" "$AUDIO_FILE" -f "$TEXT_FORMAT" --task transcribe; then
        log "::: Transcription failed"
        exit 1
    fi
}

post_process() {
    # Add your post-processing commands here
    log "::: Post-processing completed"
}

# Argument Parsing
while getopts "h" opt; do
    case $opt in
        h) display_help
           exit 0
           ;;
        \?) echo "Invalid option -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Shift off the options and optional --
shift $((OPTIND-1))

# Get Arguments
AUDIO_FILE="$1"
TEXT_FORMAT="${2:-txt}"
MODEL="${3:-$DEFAULT_MODEL}"

check_dependencies
validate_input
transcribe
post_process
