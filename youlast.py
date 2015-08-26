#!/usr/bin/env python2
from __future__ import unicode_literals

# Last.FM API libraries
import time
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

# Retrieve tracklist from Last.FM station

lastfm_username = "your_username"

while True:
  # Last.fm servers reply with a 500 error quite often, we need to catch it and retry
  try:
    response = urllib2.urlopen("http://www.last.fm/player/station/user/" + lastfm_username + "/mix")
  except urllib2.HTTPError:
    print("Is Last.fm down? Trying again in 5 seconds...")
    time.sleep(5)
    continue

  # Get and decode response
  json_tracklist = response.read()
  tracklist = json.loads(json_tracklist)

  # Validate tracklist
  if not "playlist" in tracklist:
    print("No playlist received from Last.fm")
    time.sleep(5)
    continue
  if len(tracklist["playlist"]) == 0:
    print("Empty playlis received from Last.fm")
    time.sleep(5)
    continue

  # Iterate over tracks to play them
  for track in tracklist["playlist"]:
    # Last.fm returns an array of artist, so we need to be prepared
    # to parse more songs with more than one artist
    artist = track["artists"][0]["name"]
    for i in range(1, len(track["artists"])):
      artist += ", " + track["artists"][i]["name"]

    # We print song name even before a download link is actually found
    # so we can know which song had to be played even if no donwload link
    # was found
    print("Playing " + artist + " - " + track["name"])

    yt_id = None

    # We first check if Last.fm has already provided us with a YouTube link
    for link in track["playlinks"]:
      if link["affiliate"] == "youtube":
        yt_id = link["id"]

    # If Last.fm has not provided a donwload link, try to find a video by ourselves
    if yt_id is None:
      print("No YouTube link provided, looking for one")

      youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

      search = youtube.search().list(
        q=track["artists"][0]["name"] + " - " + track["name"],
        part="id",
        maxResults=1,
        # Limit search to Music category
        videoCategoryId="sGDdEsjSJ_SnACpEvVQ6MtTzkrI/nqRIq97-xe5XRZTxbknKFVe5Lmg",
        safeSearch="none",
        type="video",
        videoLicense="any",
        videoEmbeddable="any"
      ).execute()

      videos = search["items"]
      if len(videos) != 1:
        print("No videos found. Skipping.")
        continue
      else:
        yt_id = search["items"][0]["id"]["videoId"]

    ydl_opts = {
      'format': 'bestaudio',
      'logtostderr': True,
      'outtmpl': '/tmp/%(id)s',
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    try:
      ydl.download(["https://www.youtube.com/watch?v=" + yt_id])
    except youtube_dl.utils.DownloadError:
      print("Song download failed. Skipping.")
      continue

    song = AudioSegment.from_file("/tmp/" + yt_id)
    play(song)
    remove("/tmp/" + yt_id)
