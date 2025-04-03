#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests"]
# ///

"""
Adds an article to Readwise Reader.
"""

import os
import sys
import argparse
import shutil
import json
import requests
from urllib.parse import urlparse
import logging

# Setup basic configuration for logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

API_ENDPOINT = "https://readwise.io/api/v3/save/"

def check_uv_installed():
    """Check if uv is installed on the system."""
    if not shutil.which("uv"):
        logging.error("UV is not installed. Please install it first: https://github.com/astral-sh/uv")
        sys.exit(1)

def load_config(config_path):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        logging.warning(
            f"Config file {config_path} not found. Using environment variables."
        )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON from the configuration file.")
    return None


def check_env_vars():
    """Check if the necessary environment variables are set."""
    config = load_config(args.config) if args.config else None
    global READWISE_TOKEN, API_ENDPOINT

    if config and "READWISE_TOKEN" in config:
        READWISE_TOKEN = config["READWISE_TOKEN"]
    elif READWISE_TOKEN := os.environ.get("READWISE_TOKEN"):
        pass
    else:
        logging.error(
            "READWISE_TOKEN environment variable not set. Either export it or pass it as an argument with `--config`."
        )
        exit(1)

    if API_ENDPOINT != config.get("API_ENDPOINT", API_ENDPOINT):
        API_ENDPOINT = config.get("API_ENDPOINT", API_ENDPOINT)
    elif not API_ENDPOINT:
        logging.error("API_ENDPOINT environment variable not set.")
        exit(1)


def is_valid_url(url):
    """Validate the URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception as e:
        logging.error(f"Invalid URL: {url}. Error: {e}")
        return False


def add_article(url, tags):
    """Add an article to Readwise."""
    if not is_valid_url(url):
        logging.error("Failed to validate the provided URL.")
        exit(1)

    try:
        response = requests.post(
            url=API_ENDPOINT,
            headers={
                "Authorization": f"Token {READWISE_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"url": url, "tags": tags},
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses

        logging.info(f"Added {url} to Readwise.")
        readwise_url = response.json().get("url")
        if readwise_url:
            logging.info(f"Readwise URL: {readwise_url}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error occurred while adding article: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


def main():
    """Main function to parse arguments and add articles."""
    global args
    parser = argparse.ArgumentParser(description="Adds an article to Readwise Reader.")
    parser.add_argument("URL", help="URL of the article")
    parser.add_argument(
        "--tags", nargs="*", help="Tags to add to the article", default=[]
    )
    parser.add_argument(
        "--config",
        help="Path to config file",
        required=False,
    )
    args = parser.parse_args()

    check_env_vars()
    add_article(args.URL, args.tags)


if __name__ == "__main__":
    main()
