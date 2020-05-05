#!/usr/bin/env python

import os
import http.server

import socketserver


def start_server():
  from secrets import port

  web_dir = os.path.join(os.path.dirname(__file__), 'Videos')
  os.chdir(web_dir)

  handler = http.server.SimpleHTTPRequestHandler

  with socketserver.TCPServer(("", port), handler) as httpd:
      print("Server started at port:" + str(port))
      httpd.serve_forever()

start_server()