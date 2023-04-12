#!/usr/bin/env bash

set -Eeuo pipefail

COMMANDS=("spotdl" "yt-dlp")

OUTPUT_FORMAT='{artist} - {title}'
HELP_MSG="Usage: $(basename "$0") [options] arguments

Options:
  -o, --output FORMAT    Set the output format for downloaded files (optional)
  -h, --help             Display this help message and exit

Examples:
  $(basename "$0") https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b
  $(basename "$0") -o '{artist}/{album}/{track_number} - {title}' https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b
"

python_check() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found. Please install Python 3."
        exit 1
    fi

    for package in "${COMMANDS[@]}"; do
        if ! python3 -m pip freeze 2>/dev/null | awk -F '==' '{print $1}' | grep -i "$package" &> /dev/null; then
            echo "$package not found. Please install with pip, e.g. pip install $package."
            exit 1
        fi
    done
}

system_check() {
    for cmd in "${COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "$cmd not found. Please install with a package manager, e.g. brew install $cmd."
            exit 1
        fi
    done
}

# if python_check passes, then system_check will not be called
python_check || system_check

while getopts ":o:h" opt; do
    case ${opt} in
        o)
            OUTPUT_FORMAT="$OPTARG"
            ;;
        h)
            echo "$HELP_MSG"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            echo "$HELP_MSG"
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            echo "$HELP_MSG"
            exit 1
            ;;
    esac
done

shift $((OPTIND - 1))

python3 -m spotdl "$@" --output "$OUTPUT_FORMAT"
