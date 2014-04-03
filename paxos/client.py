#!/usr/bin/env python

"""
Command-line program to allow the different hosts or clients to send
messages like ping to each other.

For instance, when starting up mininet, your end-hosts can start a ping
listen command:

  python client.py ping-listen

and then some client can send a ping with

  python client.py ping 10.0.0.1 1234 10 'Hello from a client!' &

The "10" is the amount of listen-iterations waiting for a ping-reply.
"""

import inspect
import socket
import sys
import time

from message import client
from communication import UDP

class PingClient():
  def __init__(self, udp=None):
    self.udp = udp

    if self.udp is None:
      self.udp = UDP()

  def ping(self, to, cookie, udp=None):
    """Sends a ping message."""
    data = client.ping(cookie)
    return self.udp.sendto(to, data)

  def ping_reply(self, to, cookie):
    """Sends a ping-reply message."""
    data = client.ping_reply(cookie)
    return self.udp.sendto(to, data)

def ping(ip, port, cookie="Hello, world!", udp=None):
  cl = PingClient(udp)
  print("Send ping to {}:{} w/bytes: {}".format(ip, port,
    cl.ping((ip, port), cookie)))

def ping_reply(ip, port, cookie, udp=None):
  cl = PingClient(udp)
  print("Send ping-reply to {}:{} w/bytes: {}".format(ip, port,
    cl.ping_reply((ip, port), cookie)))

def command_test():
  # ping some hosts
  ip = "10.0.0.2"
  port = 1234
  for i in range(3):
    ping(ip, port)
    if i<2: time.sleep(1)

def command_ping(ip="10.0.0.2", port=1234, repeat=10, cookie="Hello, world!"):
  port = int(port)
  repeat = int(repeat)

  udp = UDP("0.0.0.0", 1234)
  ping(ip, port, cookie, udp)

  sys.stdout.write("Waiting for ping reply ({} iterations) ".
      format(repeat))
  sys.stdout.flush()

  for i in range(repeat):
    try:
      payload, sender = udp.recvfrom()
      if client.isrecognized(payload):
        print("\nGot ping reply.... {}".format(client.unmarshal(payload)))
        break
    except socket.timeout:
      sys.stdout.write(".")
      sys.stdout.flush()

def command_ping_listen(ip="0.0.0.0", port=1234, timeout=None):
  udp = UDP(ip, int(port))

  start = time.time()

  maxwait = "forever" if timeout is None else str(timeout) + " secs"
  print("Waiting for ping message (max wait {})".format(maxwait))

  while (timeout is None) or (time.time()-start < timeout):
    try:
      sys.stdout.write(".")
      sys.stdout.flush()

      payload, sender = udp.recvfrom()

      if client.isrecognized(payload):
        message = client.unmarshal(payload)
        command, args = message

        if command == "ping":
          print("\nGot '{}' message '{}' from {}".format(command, args, sender))
          sys.stdout.flush()
          ip, port = sender
          ping_reply(ip, port, args[0], udp)
        else:
          print("Ignored command '{}'".format(command))
    except socket.timeout:
      continue
    except KeyboardInterrupt:
      print("")
      break

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
