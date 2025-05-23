#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyperclip"]
# ///

"""Returns a formatted URL for archive.is links"""

import argparse
import sys
from pathlib import Path
from typing import List, Iterator
from urllib.parse import urlparse

try:
    import pyperclip as pc
except ImportError:
    print("::: Pyperclip not installed, copying to clipboard will not work")
    print("::: Continuing without clipboard support...\n")
    pc = None


class URLFormatter:
    """Simple URL formatter for archive.is links"""

    @staticmethod
    def format_url(url: str) -> str:
        """Format a single URL for archive.is"""
        try:
            # Basic URL validation
            parsed = urlparse(url.strip())
            if not parsed.scheme or not parsed.netloc:
                return f"Error: Invalid URL format - {url}"

            # Strip query parameters and format
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return f"https://archive.is/{clean_url}"
        except Exception as e:
            return f"Error processing URL {url}: {str(e)}"


def read_urls(file_path: Path) -> Iterator[str]:
    """Read URLs from a file, skipping empty lines and comments"""
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    yield line
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)


def append_to_file(file_path: Path, formatted_urls: List[str]) -> None:
    """Append formatted URLs to the original file"""
    try:
        with open(file_path, "a") as f:
            f.write("\n\n\n# Formatted URLs\n")
            for url in formatted_urls:
                f.write(f"{url}\n")
        print(f"Formatted URLs appended to {file_path}")
    except Exception as e:
        print(f"Error appending to file {file_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Format URLs for archive.is")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--urls", nargs="+", help="One or more URLs to format")
    group.add_argument(
        "-f", "--file", type=Path, help="File containing URLs (one per line)"
    )

    args = parser.parse_args()
    formatter = URLFormatter()

    # Process URLs from command line or file
    urls = list(read_urls(args.file)) if args.file else args.urls
    formatted_urls = []

    # Process each URL
    for url in urls:
        formatted_url = formatter.format_url(url)
        formatted_urls.append(formatted_url)
        print(formatted_url)

    # Handle clipboard and file operations
    if args.urls and pc and formatted_urls:
        # Only copy to clipboard when direct URLs are provided
        pc.copy(formatted_urls[-1])  # Copy the last formatted URL
        print("URL copied to clipboard")

    # Append formatted URLs to the original file if using file input
    if args.file and formatted_urls:
        append_to_file(args.file, formatted_urls)


if __name__ == "__main__":
    main()
