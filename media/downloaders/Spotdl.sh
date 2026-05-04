#!/usr/bin/env bash

set -Eeuo pipefail

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
    if ! command -v uv &> /dev/null; then
        echo "uv not found. Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
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

    uvx spotdl "$@" --output "$OUTPUT_FORMAT"
}

main "$@"

