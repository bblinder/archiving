#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#    "requests",
#    "beautifulsoup4",
#    "colorama",
# ]
# ///

import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import re

colorama.init()
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW
BLUE = colorama.Fore.BLUE

internal_urls = set()
external_urls = set()
email_addresses = set()

total_urls_visited = 0

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def is_mail_link(href):
    """
    Checks if the link is a mailto link and extracts the email address
    """
    if href.startswith('mailto:'):
        email = href[7:]  # Remove 'mailto:' prefix
        # Basic email validation
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return email
    return None

def get_all_website_links(url):
    """
    Returns all URLs and email addresses found on `url`
    """
    urls = set()
    domain_name = urlparse(url).netloc
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"{GRAY}[!] Error: {e}{RESET}")
        return urls

    # Using find_all() instead of findAll()
    for a_tag in soup.find_all("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        # Check for email links
        email = is_mail_link(href)
        if email:
            if email not in email_addresses:
                print(f"{BLUE}[+] Email found: {email}{RESET}")
                email_addresses.add(email)
            continue

        # Handle regular URLs
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        if not is_valid(href):
            continue
        if href in internal_urls:
            continue
        if domain_name not in href:
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls

def crawl(url, max_urls=50):
    """
    Crawls a web page and extracts all links and email addresses.
    """
    global total_urls_visited
    total_urls_visited += 1
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    links = get_all_website_links(url)
    for link in links:
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Link and Email Extractor Tool with Python")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-urls", help="Number of max URLs to crawl, default is 30.", default=30, type=int)

    args = parser.parse_args()
    url = args.url
    max_urls = args.max_urls

    crawl(url, max_urls=max_urls)

    print("\n=== Summary ===")
    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total Email addresses:", len(email_addresses))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))
    print("[+] Total crawled URLs:", total_urls_visited)

    domain_name = urlparse(url).netloc

    # Save the results to files
    with open(f"{domain_name}_internal_links.txt", "w") as f:
        for internal_link in internal_urls:
            print(internal_link.strip(), file=f)

    with open(f"{domain_name}_external_links.txt", "w") as f:
        for external_link in external_urls:
            print(external_link.strip(), file=f)

    with open(f"{domain_name}_email_addresses.txt", "w") as f:
        for email in email_addresses:
            print(email.strip(), file=f)
