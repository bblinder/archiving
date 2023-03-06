#!/usr/bin/env python3

# simple script to extract links from a web page.

import argparse

import requests
from bs4 import BeautifulSoup


# @Gooey
def extract_links():
    parser = argparse.ArgumentParser(description="List the URLs on a page")
    parser.add_argument(
        "url", help="The URL of the page we're extracting links from", type=str
    )
    args = vars(parser.parse_args())

    url = args["url"]
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, "html.parser")

    urls = []
    for link in soup.find_all("a"):
        print(link.get("href"))


if __name__ == "__main__":
    extract_links()
