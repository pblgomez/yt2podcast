#!/usr/bin/env python

import argparse
import opml
import re
import feedparser as fp
import os
import http.server
import socketserver
import datetime
import subprocess
import urllib
from secrets import vids




def substract_subs(inputfile):
  nested = opml.parse(inputfile)
  subs = len(nested[0])

  titles = []
  urls = []
  i = 0
  while i < subs:
    title = nested[0][i].text
    # Remove special characters
    title = re.sub(r'[^A-Za-z0-9]+', '', title)
    url = nested[0][i].xmlUrl
    i += 1
    urls.append(url)
    titles.append(title)
  return (urls, titles, subs)


def download_videos(urls, subs, vids):
  # create_rss()
  i = 0
  while i < subs:
    # parse YouTube feed
    rss = fp.parse(urls[i])

    # print(rss.entries[i].author_detail)
    #Create rss
    create_rss(rss.feed.author, rss.feed.link)

    y = 0
    for item in rss.entries:
      if y < vids:
        # We download the video using youtube-dl
        p=subprocess.Popen(['youtube-dl',item['link'],'--output','Videos/%(uploader)s/%(title)s.%(ext)s','--ignore-errors','--add-metadata','--format','best+best','--download-archive','Videos/archive.txt','--dateafter','20200101'])
        p.wait()

        # We capture the real filename on disk
        link = subprocess.Popen(
            [
                'youtube-dl', item['link'], '--get-filename', '--output',
                'Videos/%(uploader)s/%(title)s.%(ext)s', '--format', 'best+best'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        link, err = link.communicate()
        del err

        link = str(link)
        link = link.replace("b'Videos/", "")
        link = link.replace('b"Videos/', '')
        link = link.replace("\\n'", "")
        link = link.replace("\\n\"", "")

        # Fix for unicode shit
        link = link.encode().decode('unicode-escape').encode('latin1').decode(
            'utf-8')

        #Get thumbnail of the video
        # print(item['media_thumbnail'])
        thumb_vid = str(item['media_thumbnail'])
        thumb_vid = thumb_vid.split(",")
        thumb_vid = thumb_vid[0].split(' ')
        thumb_vid = thumb_vid[1].replace("'", "")
        # print(thumb_vid)
        fill_rss(item['author'], item['title'], item['link'], link,
                 item['published'][0:16], item['summary'], thumb_vid)
        y += 1
    finish_rss(rss.feed.author)
    i += 1


# Def to get the lenght of the videos
def get_length(filename):
  filename = "Videos/" + filename
  result = subprocess.run(
      [
          "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
          "default=noprint_wrappers=1:nokey=1", filename
      ],
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT)
  return float(result.stdout)


def get_info(filename):
  # Get lenght of video
  duration = get_length(filename)
  duration = str(datetime.timedelta(seconds=duration))[:7]
  # Get filesize
  file_size = os.path.getsize("Videos/" + filename)
  return (duration, file_size)


def create_rss(author, link):
  now = datetime.datetime.now()
  now = now.strftime("%a") + "," + now.strftime("%d") + " " + now.strftime(
      "%b") + " " + now.strftime("%Y") + " " + now.strftime("%X")

  # Contenido inicial
  rss_create_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{author}</title>
    <link>{link}</link>
    <description>Podcast version of {author}</description>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{author}</itunes:author>'''

  # Write the initial file
  rss_file = "Videos/" + author + "/rss.xml"
  os.makedirs(os.path.dirname(rss_file), exist_ok=True)
  with open(rss_file, "w") as rss_out:
    rss_out.write(rss_create_content)


def fill_rss(author, title, link_orig, link, published, summary, thumb_vid):
  from secrets import host, port

  title = title.replace("&", "&#38;")
  summary = summary.replace("&", "&#38;")

  print(link)

  # Check if file exist
  if (os.path.isfile("Videos/" + link)):
    duration, file_size = get_info(link)

    # fix link name in for web
    link = urllib.parse.quote(link)

    rss_fill_content = f'''
      <item>
        <guid>"{link}"</guid>
        <title>{title}</title>
        <link>{link_orig}</link>
        <description>{summary}</description>
        <pubDate>{published}</pubDate>
        <enclosure url="{host}:{port}/{link}" length="{file_size}" type="video/mp4"></enclosure>
        <itunes:author>{author}</itunes:author>
        <itunes:subtitle>{title}</itunes:subtitle>
        <itunes:summary>{summary}</itunes:summary>
        <itunes:image href="{thumb_vid}"></itunes:image>
        <itunes:duration>{duration}</itunes:duration>
      </item>
  '''

    rss_file = "Videos/" + author + "/rss.xml"
    with open(rss_file, "a") as rss_out:
      rss_out.write(rss_fill_content)


def finish_rss(author):
  rss_finish_content = '''  </channel>
</rss>'''
  rss_file = "Videos/" + author + "/rss.xml"
  with open(rss_file, "a") as rss_out:
    rss_out.write(rss_finish_content)


def start_server():
  from secrets import port

  web_dir = os.path.join(os.path.dirname(__file__), 'Videos')
  os.chdir(web_dir)

  handler = http.server.SimpleHTTPRequestHandler

  with socketserver.TCPServer(("", port), handler) as httpd:
      print("Server started at port:" + str(port))
      httpd.serve_forever()
  # Handler = http.server.SimpleHTTPRequestHandler
  # httpd = socketserver.TCPServer(("", port), Handler)
  # print("serving at port", port)
  # httpd.serve_forever()


### Arguments
parser = argparse.ArgumentParser(
    description='Converts youtube subscriptions opml to rss podcast')
parser.add_argument(
    '-i',
    '--input',
    required=False,
    help='input filename and/or full path',
    type=str,
    dest='inputfile')
args = parser.parse_args()

if args.inputfile:
  inputfile = args.inputfile
else:
  inputfile = 'subscription_manager.opml'
##################################

urls, titles, subs = substract_subs(inputfile)



download_videos(urls, subs, vids)

start_server()