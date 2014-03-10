import logging

log = logging.getLogger('paxos')

def set_defaults():
  fmt = "%(asctime)s %(levelname)s %(message)s"
  datefmt = "%Y-%m-%d %H:%M:%S"
  logging.basicConfig(format=fmt, datefmt=datefmt)
  setLevel()

def setLevel(level=logging.INFO):
  log.setLevel(level)

set_defaults()
