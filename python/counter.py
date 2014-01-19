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

from util import (TcpClient, TcpClientError, writeln)
import argparse
import os
import sys
import time

def argparser():
  p = argparse.ArgumentParser(description="A simple counter")
  p.add_argument("--start", type=int, default=0,
                 help="Start value (integer)")
  p.add_argument("--stop",  type=int,
                 help="Stop value (integer)", default=None)
  p.add_argument("--sleep", type=int, default=1000,
                 help="Sleep value in ms between each print")
  p.add_argument("--host", type=str, default=None,
                 help="Specify host to send TCP messages to.")
  p.add_argument("--port", type=int, default=1234,
                 help="Specify which port to send TCP messages to.")
  return p

def main(args):
  counter = count(start=args.start,
                  stop=args.stop,
                  pause_ms=args.sleep)

  if args.host is not None:
    try:
      to_tcp(args.host, args.port, counter)
    except TcpClientError, e:
      writeln("Socket error: %s" % e, sys.stderr)
      sys.exit(1)
  else:
    to_console(counter)

def to_console(generator):
  """Sends generator items as strings to console."""
  for n in generator:
    writeln(str(n))

def to_tcp(host, port, generator):
  """Sends generator items as strings to remote host."""
  writeln("Connecting to %s:%d" % (host, port))

  with TcpClient(host, port) as tcp:
    for msg in generator:
      writeln("Sending '%s'" % str(msg))
      tcp.send("%s\r\n" % str(msg))

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

  def finished(number):
    if stop is None:
      return False # never stop
    else:
      return number >= stop

  while not finished(n):
    yield n
    if not finished(n+1):
      time.sleep(pause_ms/1000.0)
    n += 1

if __name__ == "__main__":
  try:
    main(argparser().parse_args())
  except KeyboardInterrupt:
    writeln()
