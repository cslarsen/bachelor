from threading import Thread
import json
import time

from acceptor import Acceptor
from proposer import Proposer
import log

def trap_sigint(signum, frame):
  raise KeyboardInterrupt()

def json_load(filename):
  """Parse a JSON file and return result."""
  with open(filename, "rt") as f:
    return json.loads("\n".join(f.readlines()))

if __name__ == "__main__":
  conf = json_load("config.json")

  acceptors = []
  for addr in conf["acceptors"]:
    ip, port = addr
    a = Acceptor(ip, port, conf["proposers"], conf["learners"])
    acceptors.append(a)
    log.info("Created acceptor {}".format(a))

  proposers = []
  for addr in conf["proposers"]:
    ip, port = addr
    p = Proposer(ip, port, conf["acceptors"])
    proposers.append(p)
    log.info("Created proposer {}".format(p))

  try:
    threads = []

    log.info("Starting {} acceptors".format(len(acceptors)))
    for a in acceptors:
      t = Thread(target = a.loop)
      t.start()
      threads.append(t)

    log.info("Starting {} proposers".format(len(proposers)))
    for p in proposers:
      t = Thread(target = p.loop)
      t.start()
      threads.append(t)

    while True:
      time.sleep(0.5)
  except KeyboardInterrupt:
    log.info("Stopping threads")
    for p in acceptors + proposers:
      p.stop = True
    for t in threads:
      t.join()
  log.info("Exiting main thread")
