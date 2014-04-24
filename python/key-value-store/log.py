"""
On import, sets up the logger.
"""

import logging

default_level = logging.INFO
logger = None

def set_defaults():
  global logger
  fmt = "%(asctime)s %(levelname)s %(message)s"
  datefmt = "%Y-%m-%d %H:%M:%S"
  logging.basicConfig(format=fmt, datefmt=datefmt)
  logger = logging.getLogger()
  setLevel()

def setLevel(level=default_level):
  logger.setLevel(level)

def turnOff():
  logger.propagate = False
  logger.setLevel(logging.CRITICAL)

def turnOn():
  logger.propagate = True

def _format(*messages):
  return "".join(map(str, *messages))

def info(*messages):
  logger.info(_format(messages))

def warn(*messages):
  logger.warn(_format(messages))

def error(*messages):
  logger.error(_format(messages))

def debug(*messages):
  logger.debug(_format(messages))

def critical(*messages):
  logger.critical(_format(messages))

set_defaults()
