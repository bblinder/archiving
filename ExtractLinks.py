#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["httpx", "bs4"]
# ///

"""A simple utility to extract links from a webpage."""

import argparse
import httpx
from bs4 import BeautifulSoup

def extract_links():
   parser = argparse.ArgumentParser(description="List the URLs on a page")
   parser.add_argument(
       "url", help="The URL of the page we're extracting links from", type=str
   )
   args = vars(parser.parse_args())

   url = args["url"]
   try:
       response = httpx.get(url)
       response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
       soup = BeautifulSoup(response.text, "html.parser")

       urls = []
       for link in soup.find_all("a"):
           href = link.get("href")
           if href:
               print(href)

   except httpx.HTTPStatusError as e:
       print(f"HTTP error occurred: {e}")
   except Exception as e:
       print(f"An error occurred: {e}")


if __name__ == "__main__":
   extract_links()
