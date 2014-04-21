#!/usr/bin/env python

"""Search for incorrect usage of label/caption, i.e. label should ALWAYS
come AFTER caption.

Usage: grep_incorrect_labels.py *.tex

To scan all files from the current directory and downwards:

    grep_incorrect_labels.py `find . -name '*.tex'`

Incorrect order of caption/label will lead to incorrect reference numbers
and hyperlink (hyperref) locations for them.

CORRECT:

  \caption{...}
  \label{...}

INCORRECT:

  \label{...}
  \caption{...}

Yes, this could probably be a one-liner using pcregrep or sed, but I
couldn't get that to work on two consecutive lines (I got matches for big
ranges of lines).

Put in the public domain by the author,
Christian Stigen Larsen
2014-04-21
"""

import re
import sys

def grep_incorrect_label(filename):
  res = False
  with open(filename, "rt") as f:
    label = re.compile(".*\\label.*")
    caption = re.compile(".*\\caption.*")

    prev_label = False
    prev_no = 0
    prev_line = ""

    for no, line in enumerate(f.readlines()):
      line = line.rstrip() # remove newline

      # Search for \caption right after \label
      if prev_label and caption.match(line):
        # Caption found after label
        print("%s:%d:%s" % (filename, 1+prev_no, prev_line))
        print("%s:%d:%s" % (filename, 1+no, line))
        prev_label = False
        res = True
        continue

      # Search for \label
      if label.match(line):
        prev_label = True
        prev_no = no
        prev_line = line
      else:
        prev_label = False

  return res

if __name__ == "__main__":
  res = False
  for f in sys.argv[1:]:
    res |= grep_incorrect_label(f)

  if res:
    print("")
    print("------------------------------------------------------------------------")
    print("Remember: For correct LaTeX references, \\caption must come BEFORE \\label")
    print("------------------------------------------------------------------------")
    print("")
