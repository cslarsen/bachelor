#!/usr/bin/env python

import pickle
import sys
import time

from communication import UDP

class PingClient():
  def __init__(self):
    pass

  def ping(self, to, cookie):
    """Sends a ping message."""
    udp = UDP()
    return udp.sendto(to, pickle.dumps(("PING-MESSAGE", "PING", cookie)))

def ping(ip, port, cookie="Hello, world!"):
  client = PingClient()
  print("Send ping to {}:{} w/bytes: {}".format(ip, port,
    client.ping((ip, port), cookie)))

def command_test():
  # ping some hosts
  ip = "10.0.0.2"
  port = 1234
  client = PingClient()
  for i in range(3):
    ping(ip, port)
    if i<2: time.sleep(1)

def command_ping(ip="10.0.0.2", port=1234, repeat=3):
  port = int(port)
  repeat = int(repeat)

  client = PingClient()

  for i in range(repeat):
    ping(ip, port)
    if i<(repeat-1):
      time.sleep(1)

if __name__ == "__main__":
  commands = {"test": command_test,
              "ping": command_ping}

  if len(sys.argv) < 2:
    print("Usage: clients <command> <argument (s)>")
    print("Known commands:")
    for cmd in commands.keys():
      print("  " + cmd)
    sys.exit(1)

  command = sys.argv[1]
  if not command in commands:
    print("Unknown command: " + sys.argv[1])
    sys.exit(1)
  else:
    func = commands[command]
    func(*sys.argv[2:])
