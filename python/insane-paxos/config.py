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

class Paxos(object):
  """A set of Paxos agents."""
  def __init__(self, acceptors, proposers, learners):
    self.a = acceptors
    self.p = proposers
    self.l = learners

    # Pick the first proposer as a leader
    self.leader = proposers[0]

    # Set up threads
    self.threads = []
    for t in self.a + self.p + self.l:
      if not t is self.leader:
        self.threads.append(Thread(target = t.loop))

  def start(self):
    """Starts all threads and waits until all agents are in the receive loop."""
    log.info("Starting {0} threads".format(len(self.threads)))
    for t in self.threads:
      t.start()

    # Except for the leader, wait until all of their stop properties have a
    # value.
    for t in self.a + self.p + self.l:
      if not t is self.leader:
        while t.stop is None:
          pass

  def stop(self):
    """Tell all agents to stop and join the threads."""
    sys.stdout.write("\n")
    sys.stdout.flush()
    log.info("Stopping {0} threads".format(len(self.threads)))

    for p in self.a + self.p + self.l:
      p.stop = True

    for t in self.threads:
      if t.ident is not None:
        t.join()

  def leader_prepare(self, value):
    """Starts a Paxos execution, wanting to reach consensus for the given
    value."""
    self.leader.v = value
    self.leader.crnd = self.leader.pickNext(self.leader.crnd) # needed? TODO

    # Send a prepare to all acceptors
    for acceptor in self.a:
      self.leader.prepare(acceptor.udp.address, self.leader.crnd)

    # TODO: Block here until we've reached consensus, or something like
    # that.

  def leader_loop(self):
    """Start leader loop."""
    while not self.leader.stop:
      try:
        self.leader.receive()
      except socket.timeout:
        sys.stdout.write("x")
        sys.stdout.flush()
      except KeyboardInterrupt:
        paxos.stop()

if __name__ == "__main__":
  conf = json_load("config.json")

  acceptors = []
  for addr in conf["acceptors"]:
    ip, port = addr
    a = Acceptor(ip, port, conf["proposers"], conf["learners"])
    acceptors.append(a)
    log.info("Created {0}".format(a))

  proposers = []
  for addr in conf["proposers"]:
    ip, port = addr
    p = Proposer(ip, port, conf["acceptors"])
    proposers.append(p)
    log.info("Created {0}".format(p))

  learners = []

  paxos = Paxos(acceptors, proposers, learners)
  paxos.start()
  paxos.leader_prepare(5)
  paxos.leader_loop()
