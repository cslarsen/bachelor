#!/usr/bin/env python

"""
Prints 0, 1, 2, 3, ... to the console.

Can be used with `nc` to submit sequence numbers in TCP packets.
"""

import argparse
import os
import sys
import time

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
    sys.stdout.write("%d\n" % n)
    sys.stdout.flush()
    if not_finished(n+1):
      time.sleep(pause_ms/1000.0)
    n += 1

def argparser():
  p = argparse.ArgumentParser(description="A simple counter")

  p.add_argument("--start", type=int, default=0,
                 help="Start value")

  p.add_argument("--stop",  type=int,
                 help="Stop value", default=None)

  p.add_argument("--sleep", type=int, default=1000,
                 help="Sleep value in ms between each print")

  return p

if __name__ == "__main__":
  args = argparser().parse_args()
  count(start=args.start, stop=args.stop, pause_ms=args.sleep)
