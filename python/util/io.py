"""
General module that contains utilities to work with standard IO.
"""

import sys

def write(message="", where=sys.stdout):
  """Write message to output and flush stream."""
  where.write(message)
  where.flush()

def writeln(message="", where=sys.stdout):
  """Write message with CRLF to output and flush stream."""
  write("%s\r\n" % str(message))
