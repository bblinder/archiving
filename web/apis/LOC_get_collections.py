#!/usr/bin/env python3

"""
Retrieves and displays all collections from the Library of Congress API.

It fetches collections data, handles pagination, and prints the title of each collection to the console.
"""

import argparse
import json
import requests
import sys
from time import sleep


def fetch_collections(verbose=False, output_file=None, delay=0.5):
    """
    Fetch and process all collections from the Library of Congress API with proper error handling.

    Args:
        verbose (bool): If True, prints additional information during processing
        output_file (str): Optional path to save results as JSON
        delay (float): Delay between API requests in seconds

    Returns:
        int: 0 for success, 1 for failure
    """
    loc_url = "https://www.loc.gov/collections/?fo=json"
    session = requests.Session()
    all_collections = []

    try:
        # Initial request
        if verbose:
            print("Starting API requests to Library of Congress...")

        response = session.get(loc_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        collections_json = response.json()

        page_count = 1
        total_collections = 0

        while True:
            if verbose:
                print(f"Processing page {page_count}...")

            # Process collections on current page
            for collection in collections_json.get("results", []):
                title = collection.get('title', 'Untitled Collection')
                print(f"- {title}")
                total_collections += 1

                if output_file:
                    all_collections.append(collection)

            # Check for next page
            next_page = collections_json.get("pagination", {}).get("next")
            if not next_page:
                break

            # Rate limiting, respectfully.
            sleep(delay)

            # Fetch next page
            response = session.get(next_page)
            response.raise_for_status()
            collections_json = response.json()
            page_count += 1

        print(f"\nCompleted! Retrieved {total_collections} collections across {page_count} pages.")

        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_collections, f, indent=2)
                print(f"Results saved to {output_file}")
            except IOError as e:
                print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
                return 1

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Library of Congress API: {e}", file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(f"Error processing API response: {e}", file=sys.stderr)
        return 1

    return 0


def fetch_specific_collection(collection_name, verbose=False):
    """
    Fetch and display detailed information about a specific collection.

    Args:
        collection_name (str): Name of the collection to retrieve
        verbose (bool): If True, prints additional information during processing

    Returns:
        int: 0 for success, 1 for failure
    """
    # URL-encode the collection name for the API request
    import urllib.parse
    encoded_name = urllib.parse.quote(collection_name)
    loc_url = f"https://www.loc.gov/{encoded_name}/?fo=json"

    try:
        if verbose:
            print(f"Fetching information for collection: {collection_name}")

        response = requests.get(loc_url)
        response.raise_for_status()
        collection_data = response.json()

        # Check if we got results
        if "results" not in collection_data or not collection_data["results"]:
            print(f"No information found for collection: {collection_name}")
            return 1

        # Display collection details
        collection = collection_data["results"][0]
        print("\nCollection Details:")
        print(f"Title: {collection.get('title', 'N/A')}")
        print(f"URL: {collection.get('url', 'N/A')}")

        # Display additional metadata if available
        if "item" in collection:
            print("\nMetadata:")
            for key, value in collection["item"].items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                print(f"  {key}: {value}")

        # Display description if available
        if "description" in collection:
            print("\nDescription:")
            print(collection["description"])

        return 0

    except requests.exceptions.RequestException as e:
        print(f"Error fetching collection data: {e}", file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(f"Error processing API response: {e}", file=sys.stderr)
        return 1


def load_collection_from_file(file_path, collection_name):
    """
    Load a specific collection from a previously saved JSON file.

    Args:
        file_path (str): Path to the JSON file containing collections
        collection_name (str): Name of the collection to find

    Returns:
        dict or None: Collection data if found, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            collections = json.load(f)

        # Find the collection by name (case-insensitive)
        collection_name = collection_name.lower()
        for collection in collections:
            if collection.get('title', '').lower() == collection_name:
                return collection

        return None
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading from file {file_path}: {e}", file=sys.stderr)
        return None


def display_collection(collection):
    """Display details of a collection."""
    if not collection:
        return

    print("\nCollection Details:")
    print(f"Title: {collection.get('title', 'N/A')}")
    print(f"URL: {collection.get('url', 'N/A')}")

    # Display additional metadata if available
    for key, value in collection.items():
        if key not in ['title', 'url']:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            print(f"\n{key}:")
            print(f"  {value}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Retrieve collections from the Library of Congress API",
        epilog="Example: ./LOC_get_collections.py --output collections.json --verbose"
    )

    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="Display detailed progress information")

    parser.add_argument("-o", "--output",
                        metavar="FILE",
                        help="Save collections to a JSON file")

    parser.add_argument("-d", "--delay",
                        type=float,
                        default=0.5,
                        help="Delay between API requests in seconds (default: 0.5)")

    parser.add_argument("-c", "--collection",
                        metavar="NAME",
                        help="Retrieve information about a specific collection")

    parser.add_argument("-f", "--from-file",
                        metavar="FILE",
                        help="Use a saved JSON file to look up a collection (requires --collection)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    # Handle the case of retrieving a specific collection
    if args.collection:
        if args.from_file:
            # Look up collection in a saved file
            collection = load_collection_from_file(args.from_file, args.collection)
            if collection:
                display_collection(collection)
                sys.exit(0)
            else:
                print(f"Collection '{args.collection}' not found in {args.from_file}")
                sys.exit(1)
        else:
            # Fetch collection from the API
            sys.exit(fetch_specific_collection(args.collection, verbose=args.verbose))
    else:
        # Fetch all collections
        sys.exit(fetch_collections(
            verbose=args.verbose,
            output_file=args.output,
            delay=args.delay
        ))
