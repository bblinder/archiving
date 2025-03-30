#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["validators", "yaspin", "yt_dlp", "webvtt-py", "deepmultilingualpunctuation"]
# ///

"""
Convert a WebVTT subtitle file to a formatted transcript.
Useful for summarization and other NLP tasks.

Usage:
    python3 vtt_to_transcript.py <video_url or vtt_file>
"""

import argparse
import html
import logging
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Third-party imports
import validators
from yaspin import yaspin
from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Optional import handling
try:
    import webvtt
except ImportError:
    logger.error("Missing dependency: webvtt-py")
    logger.error("Install with: pip install webvtt-py")
    sys.exit(1)


class TranscriptProcessor:
    """Handles the processing of VTT files into formatted transcripts."""

    def __init__(self, delete_original: bool = False):
        self.delete_original = delete_original
        self._punctuation_model = None

    @property
    def punctuation_model(self):
        """Lazy-load the punctuation model only when needed."""
        if self._punctuation_model is None:
            try:
                from deepmultilingualpunctuation import PunctuationModel

                with yaspin(
                    text="Loading punctuation model...", color="blue"
                ) as spinner:
                    self._punctuation_model = PunctuationModel()
            except ImportError:
                logger.warning(
                    "deepmultilingualpunctuation not installed. Proceeding without punctuation restoration."
                )
                self._punctuation_model = False
        return self._punctuation_model

    def process_input(self, input_path: str) -> Optional[Path]:
        """Process the input and return the path to the output file."""
        vtt_path = self.validate_input(input_path)
        if not vtt_path:
            return None

        output_path = self.generate_output_path(vtt_path)

        with yaspin(text="Processing transcript...", color="green") as spinner:
            transcript = self.vtt_to_transcript(vtt_path)
            spinner.text = "Formatting transcript..."
            transcript = self.format_transcript(transcript)

            # Write the transcript to a file
            output_path.write_text(transcript, encoding="utf-8")

            # Delete the original VTT file if requested
            if self.delete_original:
                Path(vtt_path).unlink()

            spinner.text = f"Transcript saved to: {output_path}"
            spinner.ok("✓")

        return output_path

    def validate_input(self, input_path: str) -> Optional[str]:
        """Validate input and return path to VTT file."""
        # Check if input is a URL
        if input_path.startswith(("http://", "https://")):
            if not validators.url(input_path):
                logger.error("Invalid URL provided.")
                return None
            return self.download_vtt(input_path)

        # Check if input is a local file
        input_file = Path(input_path)
        if input_file.exists():
            if input_file.suffix.lower() != ".vtt":
                logger.error("File exists but is not a .vtt file.")
                return None
            return str(input_file)

        logger.error(
            f"Input '{input_path}' is neither a valid URL nor an existing file."
        )
        return None

    def download_vtt(self, url: str) -> Optional[str]:
        """Download a VTT file using yt-dlp."""
        subtitle_langs = ["en", "en-US", "en-GB"]

        with yaspin(text="Fetching video information...", color="yellow") as spinner:
            try:
                # First extract video info to get the title
                # We use a temporary file for redirection to avoid yaspin issues
                with tempfile.TemporaryFile(mode="w+") as tmpfile:
                    orig_stdout, orig_stderr = sys.stdout, sys.stderr
                    sys.stdout, sys.stderr = tmpfile, tmpfile

                    try:
                        with YoutubeDL({"skip_download": True, "quiet": True}) as ydl:
                            info = ydl.extract_info(url, download=False)
                            title = self.sanitize_title(info.get("title", "video"))
                    finally:
                        sys.stdout, sys.stderr = orig_stdout, orig_stderr

                spinner.text = f"Found video: {title}"

                # Configure options for subtitle download
                ydl_opts = {
                    "skip_download": True,
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": subtitle_langs,
                    "subtitlesformat": "vtt",
                    "quiet": True,
                    "outtmpl": f"{title}.%(ext)s",
                }

                # Download subtitles
                spinner.text = "Downloading subtitles..."
                with tempfile.TemporaryFile(mode="w+") as tmpfile:
                    orig_stdout, orig_stderr = sys.stdout, sys.stderr
                    sys.stdout, sys.stderr = tmpfile, tmpfile

                    try:
                        with YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            available_subs = info.get("requested_subtitles", {})
                    finally:
                        sys.stdout, sys.stderr = orig_stdout, orig_stderr

                # Check if any subtitles were downloaded
                if not available_subs:
                    spinner.fail("✗")
                    logger.error("No subtitles available for this video.")
                    return None

                # Find the first successful subtitle file
                for lang in subtitle_langs:
                    if lang in available_subs:
                        vtt_file = Path(f"{title}.{lang}.vtt")
                        if vtt_file.exists():
                            spinner.ok("✓")
                            return str(vtt_file)

                spinner.fail("✗")
                logger.error("Failed to locate downloaded subtitles.")
                return None

            except Exception as e:
                spinner.fail("✗")
                logger.error(f"Error downloading subtitles: {e}")
                return None

    def generate_output_path(self, vtt_path: str) -> Path:
        """Generate output file path based on the VTT file path."""
        input_path = Path(vtt_path)
        stem = input_path.stem
        # Remove language code if present (e.g., video.en.vtt -> video)
        if "." in stem:
            stem = stem.split(".")[0]
        return input_path.with_name(f"{stem}_transcript.txt")

    def vtt_to_transcript(self, vtt_path: str) -> str:
        """Convert VTT file to raw transcript text."""
        try:
            vtt = webvtt.read(vtt_path)

            # Extract and clean text from captions
            lines = []
            seen_lines = set()

            for caption in vtt:
                for line in caption.text.strip().splitlines():
                    clean_line = line.strip()
                    if clean_line and clean_line not in seen_lines:
                        lines.append(clean_line)
                        seen_lines.add(clean_line)

            return " ".join(lines)
        except Exception as e:
            logger.error(f"Error processing VTT file: {e}")
            return ""

    def format_transcript(self, text: str) -> str:
        """Apply formatting to the transcript text."""
        if not text:
            return ""

        # Initial text cleanup
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.!?])", r"\1", text)

        # Capitalize first letter of sentences
        text = re.sub(r"(^|\.\s+)(\w)", lambda m: m.group(1) + m.group(2).upper(), text)

        # Restore punctuation if model is available
        if self.punctuation_model:
            text = self.restore_punctuation(text)

        # Add paragraph breaks
        text = self.insert_paragraph_breaks(text)

        return text.strip()

    def restore_punctuation(self, text: str) -> str:
        """Restore punctuation using a pre-trained model."""
        if not self.punctuation_model:
            return text

        with yaspin(text="Restoring punctuation...", color="magenta") as spinner:
            try:
                # Suppress warnings from the transformer library
                import warnings

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    result = self.punctuation_model.restore_punctuation(text)
                return result
            except Exception as e:
                logger.warning(f"Failed to restore punctuation: {e}")
                return text

    def insert_paragraph_breaks(
        self, text: str, sentences_per_paragraph: int = 4
    ) -> str:
        """Insert paragraph breaks after a specified number of sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        paragraphs = []

        for i in range(0, len(sentences), sentences_per_paragraph):
            paragraph = " ".join(sentences[i : i + sentences_per_paragraph])
            if paragraph:
                paragraphs.append(paragraph)

        return "\n\n".join(paragraphs)

    @staticmethod
    def sanitize_title(title: str) -> str:
        """Sanitize a title for file naming."""
        # Replace non-alphanumeric chars with underscores, except hyphens
        sanitized = re.sub(r"[^\w\-]", "_", title)
        # Replace multiple underscores with a single one
        sanitized = re.sub(r"_+", "_", sanitized)
        # Trim underscores from start and end
        return sanitized.strip("_")


def main():
    """Main function to handle CLI arguments and process input."""
    parser = argparse.ArgumentParser(
        description="Convert WebVTT subtitles to formatted transcript."
    )
    parser.add_argument("input", help="Input video URL or VTT file path")
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete the original VTT file after processing",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-punctuation",
        action="store_true",
        help="Skip punctuation restoration (faster processing)",
    )

    args = parser.parse_args()

    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Process the input
    processor = TranscriptProcessor(delete_original=args.delete)

    # Skip punctuation model if requested
    if args.no_punctuation:
        processor._punctuation_model = False

    output_path = processor.process_input(args.input)

    if output_path:
        print(f"\nTranscript saved to: {output_path}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
