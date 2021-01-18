#!/usr/bin/env python3

import requests

loc_url = "https://www.loc.gov/collections/?fo=json"
collections_json = requests.get(loc_url).json()

while True:
    for collection in collections_json["results"]:
        print(collection["title"])
        
    next_page = collections_json["pagination"]["next"]
    if next_page is not None:
        collections_json = requests.get(next_page).json()
    else:
        break
