#!/usr/bin/env python3

import argparse
import os
import pickle
import re
from urllib.parse import parse_qs, urlparse
import time

import requests
import spotipy
import tenacity
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
from spotipy.oauth2 import SpotifyOAuth

# Load Spotify API credentials from environment variables
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("Spotify API credentials not found in environment variables.")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private",
    )
)


youtube_search_cache = {}


def authenticate_youtube_api():
    """
    Authenticating the YouTube API client.
    """
    creds = None
    token_file = "token.pickle"

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "youtube_creds.json",
                ["https://www.googleapis.com/auth/youtube.force-ssl"],
            )
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


def extract_spotify_id(url):
    """
    Extracting the Spotify playlist ID from the URL.

    Args:
        url (str): The Spotify playlist URL.

    Returns:
        str: The Spotify playlist ID if the URL is valid, otherwise None.
    """
    # Check if the URL is a valid Spotify playlist URL using regex
    pattern = r"https?://open.spotify.com/playlist/[\w]+"
    if not re.match(pattern, url):
        return None

    # Parse the URL
    parsed_url = urlparse(url)

    # Extract the playlist ID from the URL path
    playlist_id = parsed_url.path.split("/")[-1]

    return playlist_id


def get_spotify_access_token():
    """Getting Spotify access token."""
    auth_url = "https://accounts.spotify.com/api/token"
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(auth_url, data=auth_data)
    response_data = response.json()
    return response_data["access_token"]


def get_spotify_playlist_tracks(playlist_id, access_token):
    """
    Retrieves the tracks from a given Spotify playlist using the Spotify API.

    Returns a list of track titles along with the name of the
    first artist for each track.

    Args:
        playlist_id (str): The Spotify playlist ID to fetch the tracks from.
        access_token (str): A valid Spotify API access token with the
                            required scopes to access the playlist tracks.

    Returns:
        list[str]: A list of strings, where each string is a track title
                   concatenated with the first artist's name, separated by a space.
                   If the playlist ID is invalid or an error occurs, an empty list is returned.
    """
    try:
        response_data = sp.playlist(playlist_id)
    except spotipy.exceptions.SpotifyException:
        return []

    tracks = [
        item["track"]["name"] + " " + item["track"]["artists"][0]["name"]
        for item in response_data["tracks"]["items"]
    ]

    return tracks


def create_youtube_playlist(youtube, playlist_name):
    """
    Creating a YouTube playlist.
    """
    request_body = {
        "snippet": {
            "title": playlist_name,
            "description": "Playlist created from Spotify",
        },
        "status": {"privacyStatus": "private"},
    }
    response = (
        youtube.playlists().insert(part="snippet,status", body=request_body).execute()
    )
    return response["id"]


def handle_playlist_item_insertion(request_id, response, exception):
    """
    Handling the response from the YouTube API after inserting a playlist item.
    """
    if exception is not None:
        print(f"Error inserting playlist item (Request ID: {request_id}): {exception}")
    else:
        print(f"Successfully inserted playlist item (Request ID: {request_id})")


# def add_video_to_youtube_playlist(youtube, playlist_id, video_id, retries=5):
#     """
#     Adding a video to a YouTube playlist.
#     """
#     request_body = {
#         "snippet": {
#             "playlistId": playlist_id,
#             "resourceId": {"kind": "youtube#video", "videoId": video_id},
#         }
#     }
#     for i in range(retries):
#         try:
#             response = (
#                 youtube.playlistItems().insert(part="snippet", body=request_body).execute()
#             )
#             return response
#         except HttpError as error:
#             if error.resp.status == 409 and i < retries - 1:
#                 sleep_time = 2**i
#                 print(f"Retry {i + 1}: Waiting for {sleep_time} seconds before retrying...")
#                 time.sleep(sleep_time)
#             else:
#                 raise

def add_videos_to_youtube_playlist(youtube, playlist_id, video_ids):
    """
    Adding videos to a YouTube playlist using a batch request.
    """

    batch = youtube.new_batch_http_request(callback=handle_playlist_item_insertion)

    for video_id in video_ids:
        request_body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
        batch.add(
            youtube.playlistItems().insert(part="snippet", body=request_body),
            request_id=video_id,
        )
    try:
        batch.execute()
    except HttpError as error:
        print(f"Error inserting playlist items: {error}")


@tenacity.retry(
    wait=tenacity.wait_fixed(0.1),  # Wait 0.1 seconds between retries
    stop=tenacity.stop_after_attempt(5),  # Stop after 5 attempts
    reraise=True,  # Reraise the exception if retries are exhausted
)
# def search_video_on_youtube(youtube, query):
#     """Searching for a video on YouTube."""
#     if query in youtube_search_cache:
#         return youtube_search_cache[query]

#     response = (
#         youtube.search()
#         .list(q=query, part="id,snippet", type="video", maxResults=1)
#         .execute()
#     )
#     video_id = response["items"][0]["id"]["videoId"]
#     youtube_search_cache[query] = video_id
#     return video_id

def search_videos_on_youtube(youtube, queries):
    """
    Searching for videos on YouTube using a single batch request.
    """
    video_ids = []
    for query in queries:
        if query in youtube_search_cache:
            video_ids.append(youtube_search_cache[query])
        else:
            response = (
                youtube.search()
                .list(q=query, part="id,snippet", type="video", maxResults=1)
                .execute()
            )
            video_id = response["items"][0]["id"]["videoId"]
            youtube_search_cache[query] = video_id
            video_ids.append(video_id)
    return video_ids

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("url", help="Spotify playlist URL")
#     args = parser.parse_args()

#     # Get Spotify access token
#     spotify_access_token = get_spotify_access_token()

#     # Get tracks from Spotify playlist
#     spotify_playlist_id = str(extract_spotify_id(url=args.url))
#     tracks = get_spotify_playlist_tracks(spotify_playlist_id, spotify_access_token)

#     # Set up YouTube API client
#     youtube = authenticate_youtube_api()

#     # Create a YouTube playlist
#     # playlist name is the same as the Spotify playlist name
#     playlist_name = sp.playlist(spotify_playlist_id)["name"]
#     #playlist_name = "Spotify Playlist"
#     youtube_playlist_id = create_youtube_playlist(youtube, playlist_name)

#     # Add tracks to the YouTube playlist
#     for track in tracks:
#         video_ids = [search_video_on_youtube(youtube, track) for track in tracks]
#         #video_id = search_video_on_youtube(youtube, track)
#         add_videos_to_youtube_playlist(youtube, youtube_playlist_id, video_ids)


# if __name__ == "__main__":
#     main()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Spotify playlist URL")
    args = parser.parse_args()

    # Get Spotify access token
    spotify_access_token = get_spotify_access_token()

    # Get tracks from Spotify playlist
    spotify_playlist_id = str(extract_spotify_id(url=args.url))
    tracks = get_spotify_playlist_tracks(spotify_playlist_id, spotify_access_token)

    # Set up YouTube API client
    youtube = authenticate_youtube_api()

    # Create a YouTube playlist
    playlist_name = sp.playlist(spotify_playlist_id)["name"]
    youtube_playlist_id = create_youtube_playlist(youtube, playlist_name)

    # Search for videos on YouTube and add them to the playlist
    video_ids = search_videos_on_youtube(youtube, tracks)
    add_videos_to_youtube_playlist(youtube, youtube_playlist_id, video_ids)

if __name__ == "__main__":
    main()
