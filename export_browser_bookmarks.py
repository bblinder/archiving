#!/usr/bin/env python3
"""
Usage:
    To export bookmarks from a specific browser, run the script with the following command:

    python export_bookmarks.py <browser> <output_file> [--format <format>]

    Replace <browser> with the name of the browser you want to export bookmarks from (e.g., 'edge', 'safari', 'chrome', 'firefox').
    Replace <output_file> with the desired name of the output file.
    Optionally, use the --format flag to specify the format of the exported bookmarks (either 'json' or 'html'). If not provided, the default format is 'json'.

    Example:
    To export Chrome bookmarks to a JSON file named "chrome_bookmarks.json", run:

    python export_bookmarks.py chrome chrome_bookmarks.json

    To export Safari bookmarks to an HTML file named "safari_bookmarks.html", run:
"""

import os
import json
import sqlite3
from pathlib import Path
import argparse
import shutil
import plistlib

def export_edge_bookmarks():
    """Export bookmarks from Microsoft Edge."""
    bookmarks_path = Path.home() / 'Library/Application Support/Microsoft Edge/Default/Bookmarks'
    if not bookmarks_path.exists():
        raise FileNotFoundError("Edge bookmarks file not found")

    with bookmarks_path.open('r', encoding='utf-8') as file:
        return json.load(file)

def export_safari_bookmarks():
    """Export bookmarks from Safari."""
    bookmarks_path = Path.home() / 'Library/Safari/Bookmarks.plist'
    if not bookmarks_path.exists():
        raise FileNotFoundError("Safari bookmarks file not found")

    temp_copy_path = Path.home() / 'Bookmarks_temp_copy.plist'
    shutil.copy(bookmarks_path, temp_copy_path)
    temp_copy_path.chmod(0o600)  # Read and write permissions for the user

    with temp_copy_path.open('rb') as file:
        bookmarks = plistlib.load(file)

    temp_copy_path.unlink()  # Remove the temporary copy
    return bookmarks

def export_chrome_bookmarks():
    """Export bookmarks from Chrome."""
    bookmarks_path = Path.home() / 'Library/Application Support/Google/Chrome/Default/Bookmarks'
    if not bookmarks_path.exists():
        raise FileNotFoundError("Chrome bookmarks file not found")

    with bookmarks_path.open('r', encoding='utf-8') as file:
        return json.load(file)

def export_firefox_bookmarks():
    """Export bookmarks from Firefox."""
    bookmarks_path = Path.home() / 'Library/Application Support/Firefox/Profiles'
    profile_path = next(bookmarks_path.glob('*.default-release'), None)
    if not profile_path:
        raise FileNotFoundError("Firefox profile not found")

    places_sqlite = profile_path / 'places.sqlite'
    if not places_sqlite.exists():
        raise FileNotFoundError("Firefox bookmarks file not found")

    conn = sqlite3.connect(places_sqlite)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT moz_bookmarks.id, moz_bookmarks.title, moz_places.url
    FROM moz_bookmarks
    JOIN moz_places ON moz_bookmarks.fk = moz_places.id
    WHERE moz_bookmarks.type = 1
    """)

    bookmarks = [
        {"id": row[0], "title": row[1], "url": row[2]}
        for row in cursor.fetchall()
    ]

    conn.close()
    return bookmarks

def convert_to_html(bookmarks, output_file):
    """Convert bookmarks to HTML."""
    html_content = """
    <!DOCTYPE NETSCAPE-Bookmark-file-1>
    <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
    <TITLE>Bookmarks</TITLE>
    <H1>Bookmarks</H1>
    <DL><p>
    """

    if isinstance(bookmarks, dict) and "roots" in bookmarks:  # Chrome/Edge format
        def parse_bookmarks(bookmark, indent=""):
            nonlocal html_content
            if isinstance(bookmark, dict):
                if "children" in bookmark:
                    html_content += f'{indent}<DT><H3>{bookmark["name"]}</H3>\n{indent}<DL><p>\n'
                    for child in bookmark["children"]:
                        parse_bookmarks(child, indent + "    ")
                    html_content += f'{indent}</DL><p>\n'
                elif "url" in bookmark:
                    html_content += f'{indent}<DT><A HREF="{bookmark["url"]}">{bookmark["name"]}</A>\n'

        for root in bookmarks["roots"].values():
            parse_bookmarks(root)
    elif isinstance(bookmarks, list):  # Firefox format
        for bookmark in bookmarks:
            html_content += f'<DT><A HREF="{bookmark["url"]}">{bookmark["title"]}</A>\n'
    elif isinstance(bookmarks, dict):  # Safari format
        def parse_safari(bookmark, indent=""):
            nonlocal html_content
            if isinstance(bookmark, dict):
                if "Children" in bookmark:
                    html_content += f'{indent}<DT><H3>{bookmark["Title"]}</H3>\n{indent}<DL><p>\n'
                    for child in bookmark["Children"]:
                        parse_safari(child, indent + "    ")
                    html_content += f'{indent}</DL><p>\n'
                elif "URLString" in bookmark:
                    html_content += f'{indent}<DT><A HREF="{bookmark["URLString"]}">{bookmark["URIDictionary"]["title"]}</A>\n'
        parse_safari(bookmarks)

    html_content += "</DL><p>"

    with Path(output_file).open('w', encoding='utf-8') as file:
        file.write(html_content)

def append_extension(filename, extension):
    """Append the relevant extension to the filename"""
    if not filename.endswith(f".{extension}"):
        filename += f".{extension}"
    return filename

def main():
    """Export browser bookmarks."""
    parser = argparse.ArgumentParser(description='Export browser bookmarks.')
    parser.add_argument('browser', choices=['edge', 'safari', 'chrome', 'firefox'], help='The browser to export bookmarks from.')
    parser.add_argument('output_file', help='The output file to save the bookmarks.')
    parser.add_argument('--format', choices=['json', 'html'], default='json', help='The format to export bookmarks to.')

    args = parser.parse_args()

    try:
        if args.browser == 'edge':
            bookmarks = export_edge_bookmarks()
        elif args.browser == 'safari':
            bookmarks = export_safari_bookmarks()
        elif args.browser == 'chrome':
            bookmarks = export_chrome_bookmarks()
        elif args.browser == 'firefox':
            bookmarks = export_firefox_bookmarks()

        output_file = append_extension(args.output_file, args.format)

        if args.format == 'json':
            with Path(output_file).open('w', encoding='utf-8') as file:
                json.dump(bookmarks, file, indent=4)
        elif args.format == 'html':
            convert_to_html(bookmarks, output_file)

        print(f"{args.browser.capitalize()} bookmarks exported successfully to {output_file}.")
    except FileNotFoundError as e:
        print(e)
    except PermissionError as e:
        print(f"Permission denied: {e}")

if __name__ == "__main__":
    main()
