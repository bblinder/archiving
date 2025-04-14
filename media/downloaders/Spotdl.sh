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

check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found. Please install Python 3."
        exit 1
    fi

    for package in "${COMMANDS[@]}"; do
        if ! python3 -m pip show "$package" &> /dev/null; then
            echo "$package not found. Please install with pip, e.g. pip install $package."
            exit 1
        fi
    done
}

parse_arguments() {
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
}

main() {
    check_dependencies
    parse_arguments "$@"

    python3 -m spotdl "$@" --output "$OUTPUT_FORMAT"
}

main "$@"