#!/usr/bin/env bash

set -Eeuo pipefail

COMMANDS=("spotdl" "yt-dlp")

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
    # Check if the commands are installed as system commands (e.g. Homebrew)
    for cmd in "${COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "$cmd not found. Please install with a package manager, e.g. brew install $cmd."
            exit 1
        fi
    done
}


# if python_check passes, then system_check will not be called
python_check || system_check

python3 -m spotdl "$@" --output '{artist} - {title}'


## TODO
## use getops to provide options
## See: https://www.redhat.com/sysadmin/arguments-options-bash-scripts

