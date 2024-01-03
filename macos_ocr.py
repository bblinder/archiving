#!/usr/bin/env python3

"""
Enhanced script to run native OCR using the OCR Text shortcut on MacOS/iOS with improved error handling and logging.
"""

import subprocess
import argparse
import sys
import platform
import logging
import os

SHORTCUT_NAME = "Extract Text"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def is_macos():
    """
    Check if the operating system is MacOS.
    Returns:
        bool: True if the OS is MacOS, False otherwise.
    """
    return platform.system() == "Darwin"


def validate_file_path(file_path):
    """
    Validate if the provided file path exists and is accessible.
    Args:
        file_path (str): Path of the file to check.
    Raises:
        ValueError: If the file path is invalid or inaccessible.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File path does not exist: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")


def run_ocr(file_path):
    """
    Run OCR on a file using the OCR Text shortcut.
    Args:
        file_path (str): Path to the file for OCR processing.
    """
    if not is_macos():
        logging.error("This script can only be run on MacOS.")
        sys.exit(1)

    try:
        validate_file_path(file_path)
        command = ["shortcuts", "run", SHORTCUT_NAME, "-i", file_path]
        ocr_out = subprocess.check_output(command).decode('utf-8')
        logging.info(ocr_out)
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running the OCR: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logging.error(e)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run OCR on a file using MacOS's OCR Text shortcut.")
    parser.add_argument("file", help="Path to the file for OCR.")
    args = parser.parse_args()

    run_ocr(args.file)


if __name__ == "__main__":
    main()
