#!/usr/bin/env python3

# Adapted from a found script.
# Downloads all images on a given web page.
# To merely see/print the image URLs, see the `list_image_Urls.py` script.

# TODO: account for pages that lazy load.

import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_images(url):
    """
    Returns all image URLs on a single `url`
    """
    soup = bs(requests.get(url).content, "html.parser")
    urls = []
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            continue
        # make the URL absolute by joining domain with the URL that is just extracted
        img_url = urljoin(url, img_url)
        # remove URLs like '/hsts-pixel.gif?c=3.2.5'
        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass
        # finally, if the url is valid
        if is_valid(img_url):
            urls.append(img_url)
    return urls


def download(url, pathname):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)

    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))

    # get the file name
    filename = os.path.join(pathname, url.split("/")[-1])

    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(
        response.iter_content(1024),
        f"Downloading {filename}",
        total=file_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    )
    with open(filename, "wb") as f:
        for data in progress:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))


def download_images(url, path):
    # get all images
    imgs = get_all_images(url)
    for img in imgs:
        # for each img, download it
        download(img, path)


# Now onto the actual work
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="This script downloads all images from a web page"
    )
    parser.add_argument(
        "url", help="The URL of the web page you want to download images"
    )
    parser.add_argument(
        "-p",
        "--path",
        help="The directory you want to store your images, default is the domain of URL passed",
    )

    args = parser.parse_args()
    url = args.url
    path = args.path

    if not path:
        # if path isn't specified, use the domain name of that url as the folder name
        path = urlparse(url).netloc

    download_images(url, path)
