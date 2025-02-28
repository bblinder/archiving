#!/usr/bin/env bash

set -Eeuo pipefail

# Define script directory for absolute path operations
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)

# Default configurations
WHISPER_DIR="$HOME/Github/whisper.cpp"
MODEL="medium.en"  # Default model
DATA_DIR=""  # Will be set based on user input
FORCE_DOWNLOAD=false
SKIP_COMPILATION=false
PROMPT="" # Default prompt, based on user input
OUTPUT_FORMAT="vtt"  # Default output format

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
  echo "Performing cleanup tasks..."
  [[ -d "$TEMP_OUTPUT_DIR" ]] && rm -rf "$TEMP_OUTPUT_DIR"
}

setup_colors() {
  if [[ -t 2 ]] && [[ -z "${NO_COLOR-}" ]] && [[ "${TERM-}" != "dumb" ]]; then
    NOFORMAT='\033[0m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    ORANGE='\033[0;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    YELLOW='\033[1;33m'
  else
    NOFORMAT=''
    RED=''
    GREEN=''
    ORANGE=''
    BLUE=''
    PURPLE=''
    CYAN=''
    YELLOW=''
  fi
}

usage() {
  echo "Usage: $0 [-m model_size] [-d data_dir] [-s] [-f] [-o output_format]"
  echo "  -m, --model            Model size to download and use (default: medium.en)"
  echo "  -d, --data-dir         Directory containing the data files to process"
  echo "  -s, --skip-compilation Skip compilation check"
  echo "  -f, --force-download   Force re-download of the model"
  echo "  -p, --prompt           Specify the initial prompt"
  echo "  -o, --output-format    Specify output format (vtt or txt, default: vtt)"
  exit 1
}

parse_params() {
  while :; do
    case "${1-}" in
    -h | --help) usage ;;
    -m | --model)
      MODEL="${2-}";
      shift ;;
    -d | --data-dir)
      DATA_DIR="${2-}";
      shift ;;
    -s | --skip-compilation) SKIP_COMPILATION=true ;;
    -f | --force-download) FORCE_DOWNLOAD=true ;;
    -p | --prompt)
      PROMPT="${2-}"
      shift ;;
    -o | --output-format)
      if [[ "${2-}" == "vtt" || "${2-}" == "txt" ]]; then
        OUTPUT_FORMAT="${2-}"
      else
        echo "Invalid output format: ${2-}. Use 'vtt' or 'txt'."
        exit 1
      fi
      shift ;;
    --) shift; break ;;
    -?*) usage ;;
    *) break ;;
    esac
    shift
  done

  if [[ -z "$DATA_DIR" ]]; then
    echo "Error: Data directory is required."
    usage
  fi
}

parse_params "$@"
setup_colors

# Ensure DATA_DIR is an absolute path
DATA_DIR=$(realpath "$DATA_DIR")

# Output directory is set relative to DATA_DIR
OUTPUT_DIR="$DATA_DIR/output"
mkdir -p "$OUTPUT_DIR"

# Define and create a temporary output directory within DATA_DIR
TEMP_OUTPUT_DIR="$DATA_DIR/temp_output"
mkdir -p "$TEMP_OUTPUT_DIR"

cd "$WHISPER_DIR" || exit 1

if [ "$FORCE_DOWNLOAD" = true ] || [ ! -f "./models/${MODEL}.bin" ]; then
  echo "Downloading or re-downloading the model..."
  ./models/download-ggml-model.sh $MODEL
else
  echo "Model ${MODEL} is already downloaded."
fi

if [ "$SKIP_COMPILATION" = false ]; then
  if [ ! -f "./main" ]; then
    echo "Project not compiled, compiling now..."
    make
  else
    echo "Project already compiled."
  fi
else
  echo "Skipping compilation check as requested."
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &>/dev/null; then
  echo 'Error: ffmpeg is not installed.' >&2
  exit 1
fi

# Process files
echo "Converting files to WAV format and processing..."
media_extensions=("mp3" "wav" "m4a" "flac" "ogg" "aac" "mp4" "mov" "opus" "webm" "mkv")

for ext in "${media_extensions[@]}"; do
  for i in "$DATA_DIR"/*.${ext}; do
    [ -e "$i" ] || continue  # Skip if no files found for this extension
    f=$(basename -- "$i")
    filename="${f%.*}"
    converted_path="$OUTPUT_DIR/${filename}.wav"
    ffmpeg -i "$i" -acodec pcm_s16le -ac 1 -ar 16000 "$converted_path"

    # Temporarily copy the converted file to the Whisper directory
    cp "$converted_path" "$WHISPER_DIR/data/"

    # Run the transcription with the specified output format
    "$WHISPER_DIR/build/bin/whisper-cli" -m "$WHISPER_DIR/models/ggml-${MODEL}.bin" -l en --output-${OUTPUT_FORMAT} -pc -pp --prompt $PROMPT -f "$WHISPER_DIR/data/${filename}.wav"

    # Adjust the filename for moving based on output format
    output_ext=${OUTPUT_FORMAT}
    vtt_filename="${filename}.wav.${output_ext}"

    # Move the output file to the temporary output directory first
    if [ -f "$WHISPER_DIR/data/$vtt_filename" ]; then
        mv "$WHISPER_DIR/data/$vtt_filename" "$TEMP_OUTPUT_DIR/"
        # Then move it to its final destination
        mv "$TEMP_OUTPUT_DIR/$vtt_filename" "$OUTPUT_DIR/"
    else
        echo "${RED}Expected output file not found: $WHISPER_DIR/data/$vtt_filename${NOFORMAT}" >&2
    fi

    # Remove the copied WAV file from the Whisper directory
    rm "$WHISPER_DIR/data/${filename}.wav"
  done
done

# Cleanup the temporary output directory
rm -rf "$TEMP_OUTPUT_DIR"

echo -e "${GREEN}Transcription completed.${NOFORMAT}"
echo -e "${GREEN}Output files are available in $OUTPUT_DIR${NOFORMAT}"
