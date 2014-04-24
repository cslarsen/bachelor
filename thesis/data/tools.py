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

def read(filename, column=0, delimiter=' ', quotechar='|'):
  """Returns list of floating point numbers from the file."""
  # TODO: Add support for column and separator
  with open(filename, "rt") as f:
    rows = csv.reader(f, delimiter=' ', quotechar='|')
    vals = map(lambda row: row[column], list(rows))
    n = map(lambda num: float(num), vals)
    return n

def rms(numbers):
  """Returns root-mean-square of numbers."""
  squares = map(lambda s: s**2, numbers)
  mean = sum(squares) / len(squares)
  root = math.sqrt(mean)
  return root
