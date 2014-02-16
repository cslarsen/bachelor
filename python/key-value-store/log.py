"""
On import, sets up the logger.
"""

import logging

def set_defaults():
  fmt = "%(asctime)s %(levelname)s %(message)s"
  datefmt = "%Y-%m-%d %H:%M:%S"
  logging.basicConfig(format=fmt, datefmt=datefmt)
  setLevel()

def setLevel(level=logging.INFO):
  logging.getLogger().setLevel(level)

def _format(*messages):
  return "".join(map(str, *messages))

def info(*messages):
  logging.info(_format(messages))

def warn(*messages):
  logging.warn(_format(messages))

def error(*messages):
  logging.error(_format(messages))

def debug(*messages):
  logging.debug(_format(messages))

def critical(*messages):
  logging.critical(_format(messages))

set_defaults()
