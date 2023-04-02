#!/usr/bin/env bash

set -Eeuo pipefail
#IFS=$'\n\t'


COMMANDS="spotdl yt-dlp"

for cmd in $COMMANDS; do
    if ! command -v "$cmd" &> /dev/null ; then
    echo "$cmd not found. Please install with a package manager, e.g. brew install $cmd."
    exit 1
    fi
done

python3 -m spotdl "$@" --output '{artist} - {title}'

## TODO
## use getops to provide options
## See: https://www.redhat.com/sysadmin/arguments-options-bash-scripts

