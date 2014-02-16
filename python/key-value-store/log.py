"""
On import, sets up the logger.
"""

import logging

def set_defaults():
  fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
  datefmt = "%Y-%m-%d %H:%M:%S"
  logging.basicConfig(format=fmt, datefmt=datefmt)
  setLevel()

def setLevel(level=logging.INFO):
  logging.getLogger().setLevel(level)

def info(*messages):
  logging.info(" ".join(messages))

def warn(*messages):
  logging.warn(" ".join(messages))

def error(*messages):
  logging.error(" ".join(messages))

def debug(*messages):
  logging.debug(" ".join(messages))

def critical(*messages):
  logging.critical(" ".join(messages))

set_defaults()
