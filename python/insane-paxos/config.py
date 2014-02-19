from threading import Thread
import json
import socket
import sys

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

    for a in acceptors:
      threads.append(Thread(target = a.loop))

    for p in proposers[0:-1]:
      threads.append(Thread(target = p.loop))

    def start_threads():
      for t in threads: t.start()

    # Pick the last one to be leader, and control it here...
    leader = proposers[-1]

    # Start up!
    start_threads()

    # First, try to send a prepare to an acceptor
    crnd = 10
    leader.prepare(acceptors[0].udp.address, crnd)

    while not leader.stop:
      try:
        leader.receive()
      except socket.timeout:
        sys.stdout.write("x")
        sys.stdout.flush()

    log.info("Stopping threads")

  except KeyboardInterrupt:
    pass

  print("")
  log.info("Stopping threads")
  for p in acceptors + proposers:
    p.stop = True

  for t in threads:
    if t.ident is not None: # started?
      t.join()
