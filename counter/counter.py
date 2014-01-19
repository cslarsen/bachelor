#!/usr/bin/env python

"""
A counter that sends 0, 1, 2, 3, ... to either the console or a remote TCP
host.

The remote server can use netcat (`nc`) to receive messages, e.g.:

    remote$ nc -l 1234

You can then send to the remove server at 1.2.3.4:1234 using either

    local$ ./counter.py | nc 1.2.3.4 1234

or

    local$ ./counter.py --sleep=500 --host=1.2.3.4 --port=1234

The TCP messages are sent using the format "<number>\r\n"

Make sure the remote host is waiting to receive before starting the counter.
"""

import argparse
import os
import socket
import sys
import time

class TcpSocket():
  def __init__(self, remote_host, remote_port):
    self.host = remote_host
    self.port = remote_port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def connect(self):
    self.socket.connect((self.host, self.port))

  def send(self, data):
    return self.socket.send(data)

  def recv(self, buffer_size=1024):
    return self.socket.recv()

  def __enter__(self):
    self.connect()
    return self

  def __exit__(self, type, value, traceback):
    # Close even if we have an exception
    self.socket.close()

def count(start=0, stop=None, pause_ms=1000):
  """Start printing count messages.

  Args:
    start: Start number of sequence.
    stop: If set to None, will loop forever.
          If set to a number, will stop when
          counter reaches this number, e.g.
          count(start=0, stop=10) will print
          0,1,2,...,9 but not 10.
    pause_ms: Amount of milliseconds to wait between each message.
  """
  n = start

  def not_finished(number):
    if stop is None:
      return True # never stop
    return number<stop

  while not_finished(n):
    yield n
    if not_finished(n+1):
      time.sleep(pause_ms/1000.0)
    n += 1

def write(message, where=sys.stdout):
  """Write message to output and flush stream."""
  where.write("%s\n" % str(message))
  where.flush()

def to_console(generator):
  """Sends generator items as strings to console."""
  for n in generator:
    write(n)

def to_tcp(host, port, generator):
  """Sends generator items as strings to remote host."""
  write("Connecting to %s:%d" % (host, port))
  with TcpSocket(host, port) as tcp:
    for msg in generator:
      write("Sending '%s'" % str(msg))
      tcp.send("%s\r\n" % str(msg))

def argparser():
  p = argparse.ArgumentParser(description="A simple counter")

  p.add_argument("--start", type=int, default=0,
                 help="Start value")

  p.add_argument("--stop",  type=int,
                 help="Stop value", default=None)

  p.add_argument("--sleep", type=int, default=1000,
                 help="Sleep value in ms between each print")

  p.add_argument("--host", type=str, default=None,
                 help="Specify host to send TCP messages to.")

  p.add_argument("--port", type=int, default=1234,
                 help="Specify which port to send TCP messages to.")

  return p

def main(args):
  counter = count(start=args.start, stop=args.stop, pause_ms=args.sleep)

  if args.host is not None:
    try:
      to_tcp(args.host, args.port, counter)
    except socket.error, e:
      sys.stderr.write("Socket error: %s\n" % e)
      sys.exit(1)
  else:
    to_console(counter)

if __name__ == "__main__":
  try:
    main(argparser().parse_args())
  except KeyboardInterrupt:
    print("")
