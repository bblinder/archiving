#!/usr/bin/env python3

"""
Generates an OPML file from a list of YouTube subscriptions.

It reads the list of YouTube subscriptions from a JSON file named 'subscriptions.json',
then creates an OPML file with the subscriptions listed under the 'YouTube Channels' outline.

Usage:
1. Visit your YouTube subscriptions page and load all the subscriptions.
2. Copy the list of subscriptions as a JSON array using the provided JavaScript code:
    ```javascript
    copy(JSON.stringify(Array.from(new Set(Array.prototype.map.call(document.querySelectorAll('a.channel-link'), (link) => link.href))).filter((x) => !x.includes('/channel/')), null, 2))
    ```
3. Paste the list into a 'subscriptions.json' file.
4. Run this script to generate the OPML file.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

# Check if the 'subscriptions.json' file exists
if not os.path.isfile("subscriptions.json"):
    print("Error: 'subscriptions.json' file not found.")
    sys.exit(1)

# Load JSON data from a file
with open("subscriptions.json", "r", encoding="utf-8") as file:
    urls = json.load(file)

# Create the root element of the OPML file with the 'opml' tag
root = ET.Element("opml", version="1.0")

# Add the head section with details
head = ET.SubElement(root, "head")
title = ET.SubElement(head, "title")
title.text = "RSS subscriptions for brandon.blinderman@gmail.com"
date_created = ET.SubElement(head, "dateCreated")
date_created.text = datetime.now().strftime(
    "%a, %d %b %Y %H:%M:%S +0000"
)  # Format the current UTC time
owner_email = ET.SubElement(head, "ownerEmail")
owner_email.text = "brandon.blinderman@gmail.com"

# Create the body of the OPML file
body = ET.SubElement(root, "body")
outline = ET.SubElement(
    body, "outline", text="YouTube Channels", title="YouTube Channels"
)

# Add each URL to the OPML under the 'YouTube Channels' outline
for url in urls:
    channel_name = url.split("@")[-1]  # Extract channel name from URL
    title = f"YouTube Channel: {channel_name}"  # Create a title using the channel name
    ET.SubElement(
        outline, "outline", text=title, type="rss", xmlUrl=url, title=title, htmlUrl=url
    )

# Generate the OPML XML structure
tree = ET.ElementTree(root)
filename = f"youtube_subscriptions_{datetime.now().strftime('%Y-%m-%d')}.opml"
tree.write(filename, encoding="UTF-8", xml_declaration=True)
print(f"::: OPML file generated successfully: {filename}")
