#!/usr/bin/env python

import inspect
import socket
import sys
import time

from message import client
from communication import UDP

class PingClient():
  def ping(self, to, cookie):
    """Sends a ping message."""
    data = client.ping(cookie)
    udp = UDP()
    return udp.sendto(to, data)

  def ping_reply(self, to, cookie):
    """Sends a ping-reply message."""
    data = client.ping_reply(cookie)
    udp = UDP()
    return udp.sendto(to, data)

def ping(ip, port, cookie="Hello, world!"):
  cl = PingClient()
  print("Send ping to {}:{} w/bytes: {}".format(ip, port,
    cl.ping((ip, port), cookie)))

def ping_reply(ip, port, cookie):
  cl = PingClient()
  print("Send ping-reply to {}:{} w/bytes: {}".format(ip, port,
    cl.ping_reply((ip, port), cookie)))

def command_test():
  # ping some hosts
  ip = "10.0.0.2"
  port = 1234
  for i in range(3):
    ping(ip, port)
    if i<2: time.sleep(1)

def command_ping(ip="10.0.0.2", port=1234, repeat=3):
  port = int(port)
  repeat = int(repeat)

  udp = UDP("0.0.0.0", 1234)

  for i in range(repeat):
    ping(ip, port)
    try:
      payload, sender = udp.recvfrom()
      if client.isrecognized(payload):
        print("Got ping reply.... {}".format(payload))
    except socket.timeout:
      pass
    if i<(repeat-1):
      time.sleep(1)

def command_ping_listen(ip="0.0.0.0", port=1234, timeout=None):
  udp = UDP(ip, int(port))

  start = time.time()
  while (timeout is None) or (time.time()-start < timeout):
    try:
      maxwait = "forever" if timeout is None else str(timeout) + " secs"
      maxwait += ", waited " + str(int(time.time() - start)) + " secs"
      print("Waiting for ping message (max wait {})".format(maxwait))
      payload, sender = udp.recvfrom()

      if client.isrecognized(payload):
        message = client.unmarshal(payload)
        command, args = message
        print("Got '{}' message '{}' from {}".format(command, args, sender))
        ip, port = sender
        ping_reply(ip, port, args[0])
        break
    except socket.timeout:
      continue

def command_help():
    print("Usage: clients <command> <argument (s)>")
    print("Known commands:")
    for cmd in sorted(commands.keys()):
      print("  {} args: {}".format(cmd, inspect.getargspec(commands[cmd])))

if __name__ == "__main__":
  commands = {
      "test": command_test,
      "ping": command_ping,
      "ping-listen": command_ping_listen,
      "help": command_help,
  }

  if len(sys.argv) < 2:
    command_help()
    sys.exit(1)

  command = sys.argv[1]
  if not command in commands:
    print("Unknown command: " + sys.argv[1])
    command_help()
    sys.exit(1)
  else:
    func = commands[command]
    func(*sys.argv[2:])
    sys.exit(0)
