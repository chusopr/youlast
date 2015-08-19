#!/usr/bin/env python2

# Last.FM API libraries
import time
#import pylast
import urllib2
import json
# YouTube API libraries
import youtube_dl
from googleapiclient.discovery import build
# Playback libraries
from pydub import AudioSegment
from pydub.playback import play
from os import remove

# Your YouTube developer key from https://cloud.google.com/console
DEVELOPER_KEY = "your-api-key"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Replace with your API key and secret from http://www.last.fm/api/account
API_KEY = "your-api-key"
API_SECRET = "your-api-secret"

username = "your_username"
password_hash = "your_password"

if not "tune" in dir(pylast.LastFMNetwork):
  print("You need modified pylast library from https://github.com/chusopr/pylast/archive/pylast-stations.zip")
  exit()

network = pylast.LastFMNetwork(api_key = API_KEY, api_secret =
    API_SECRET, username = username, password_hash = pylast.md5(password_hash))
network.tune(network.get_authenticated_user().get_mix_station_url())
print("Playing " + network.get_station_name())

while True:
  # Retrieve tracklist from Last.FM station
  for track in network.get_station_tracks():
    print("Playing " + track.get_artist() + " - " + track.get_title())

    # Search song in YouTube
    yt_id = None

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    search = youtube.search().list(
      q = track.get_artist() + " - " + track.get_title(),
      part = "id",
      maxResults = 1,
      videoCategoryId = "sGDdEsjSJ_SnACpEvVQ6MtTzkrI/nqRIq97-xe5XRZTxbknKFVe5Lmg",
      safeSearch = "none",
      type = "video",
      videoLicense = "any",
      videoEmbeddable = "any"
    ).execute()

    videos = search["items"]
    if len(videos) != 1:
      print("No videos found. Skipping.")
      continue
    else:
      yt_id = search["items"][0]["id"]["videoId"]

    # Download song
    ydl_opts = {
      'format': 'bestaudio',
      'logtostderr': True,
      'outtmpl': '/tmp/%(id)s',
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    ydl.download(["https://www.youtube.com/watch?v=" + yt_id])

    # Play donwloaded song
    song = AudioSegment.from_file("/tmp/" + yt_id)
    play(song)
    remove("/tmp/" + yt_id)
