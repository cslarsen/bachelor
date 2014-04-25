"""Module for working with measurement data for plots.

Example:

  >>> from tools import *
  >>> n = read("pings.txt")
  >>> rms(n)

Note that for stuff like rms, one should rather use a good tool like R.

I mainly use this file for working with the numbers before I feed them into
R (like converting rount trip times to latencies, etc.).
"""

import csv
import math
import re

def read(filename, column=0, delimiter=' ', quotechar='|'):
  """Returns list of floating point numbers from the file."""
  # TODO: Add support for column and separator
  with open(filename, "rt") as f:
    rows = csv.reader(f, delimiter=' ', quotechar='|')
    vals = map(lambda row: row[column], list(rows))
    n = map(lambda num: float(num), vals)
    return n

def readlines(filename):
  """Returns list of lines from file."""
  with open(filename, "rt") as f:
    return map(lambda s: s.rstrip(), f.readlines())

def readpings(filename):
  """Parses ping output and returns dict of results."""
  """
  64 bytes from 10.0.0.10: icmp_req=1 ttl=64 time=245 ms
  64 bytes from 10.0.0.10: icmp_req=2 ttl=64 time=124 ms
  64 bytes from 10.0.0.10: icmp_req=3 ttl=64 time=81.4 ms
  """
  values = []
  for line in readlines(filename):
    if re.match(".*time=.*", line):
      v = line.split(" ")
      values.append(
          {"Bytes": v[0],
           "From": v[3].split(":")[0],
           "Req": v[4].split("=")[1],
           "TTL": v[5].split("=")[1],
           "RTT": v[6].split("=")[1].split(" ")[0]})
  return values

def pings2csv(filename, sep=","):
  """Converts ping data to CSV."""
  pings = readpings(filename)

  # Header
  print(sep.join(pings[0].keys()))

  # Values
  for row in pings:
    print(sep.join(row.values()))

def rms(numbers):
  """Returns root-mean-square of numbers."""
  squares = map(lambda s: s**2, numbers)
  mean = sum(squares) / len(squares)
  root = math.sqrt(mean)
  return root
