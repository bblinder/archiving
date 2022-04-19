#!/usr/bin/env python3

import argparse
import re
import requests

parser = argparse.ArgumentParser(description="Magnet link extractor tool")
parser.add_argument("url", help="The URL to extract magnet links from.")

args = parser.parse_args()
url = args.url


def get_magnet_links(url):
    r = requests.get(url)
    magnet_links = re.findall(r'magnet:\?[^\'"\s<>\[\]]+', r.text)
    return magnet_links


if get_magnet_links(url):
    with open("magnet_links.txt", "w") as f:
        for link in get_magnet_links(url):
            print(link.strip(), file=f)
