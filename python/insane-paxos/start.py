import json
import multiprocessing as mp
import random
import socket
import sys

from acceptor import Acceptor
from learner import Learner
from nodes import Nodes
from proposer import Proposer
import log

#def trap_sigint(signum, frame):
#  raise KeyboardInterrupt()

def json_load(filename):
  """Parse a JSON file and return result."""
  with open(filename, "rt") as f:
    return json.loads("\n".join(f.readlines()))

class Paxos(object):
  """A set of Paxos agents."""
  def __init__(self, addresses, A, P, L):
    self.addresses = addresses
    self.A = A
    self.P = P
    self.L = L

    # Pick the first proposer as a leader
    assert len(self.addresses.proposers) > 0
    self.leader_addr = self.addresses.proposers[0]

    # Find leader object
    for obj in self.objects:
      if (obj._ip, obj._port) == self.leader_addr:
        self.leader = obj
        break

    # Set up processes
    self.procs = []
    for t in self.A + self.P + self.L:
      # Skip leader
      if (t._ip, t._port) != self.leader_addr:
        self.procs.append(mp.Process(target=t.setup))

  @property
  def objects(self):
    """Return all acceptors, proposers and learners."""
    return self.A + self.P + self.L

  def start(self):
    """Starts all procs and waits until all agents are in the receive
    loop."""
    log.info("Starting {0} processes".format(len(self.procs)))

    # Complete instantiation of leader (binds sockets, etc.)
    self.leader.setup(loop=False)

    # Fire up the processes (we'll let the leader run in THIS process)
    for t in self.procs:
      t.start()
    log.info("Leader has id={}".format(self.leader.id))

    log.info("Waiting until all nodes are up")
    for t in self.objects:
      if (t._ip, t._port) != self.leader_addr:
        cookie = random.randint(0,9999999)
        while True:
          try:
            self.leader.ping((t._ip, t._port), cookie)
            (command, recv_cookie) = self.leader.pump()
            if command == "ping-reply" and recv_cookie == cookie:
              log.debug("{}<-{} leader on_ping(id={}, cookie={})".format(
                self.leader.id, t.id, t.id, cookie))
              break
          except socket.timeout:
            sys.stdout.write("z")
            sys.stdout.flush()
      else:
        log.info("Skipping ping to leader at {}".format(self.leader_addr))

  def stop(self):
    """Tell all agents to stop and join the processes."""
    log.info("Stopping {0} processes".format(len(self.procs)))
    self.leader.stop = True

    # Tell objects to stop looping
    for node in self.objects:
      node.stop = True

    # Wait for them to finish
    for t in self.procs:
      if t.is_alive(): # has process been started?
        t.join()
        t.terminate()

  def leader_prepare(self, value):
    """Starts a Paxos execution, wanting to reach consensus for the given
    value."""
    self.leader.setvalue(value)
    self.leader.trust(self.leader.address, self.leader.id)

    # TODO: Block here until we've reached consensus (i.e. the algorithm
    # round terminates)

  def leader_loop(self):
    """Start leader loop."""
    ip, port = self.leader.address
    log.info("Node {}: Leader listening on {}:{}".format(
      self.leader.id,
      ip,
      port))

    started = False
    while not self.leader.stop:
      try:
        # Start a Paxos algorithm instance
        if not started:
          self.leader_prepare(5)
          started = True

        self.leader.receive()
      except socket.timeout:
        sys.stdout.write("*")
        sys.stdout.flush()
      except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.leader.stop = True
      except Exception, e:
        log.exception(e)
        raise e
    log.info("Leader stopped")

if __name__ == "__main__":
  cfg = json_load("config.json")
  acceptors = cfg["acceptors"]
  proposers = cfg["proposers"]
  learners = cfg["learners"]

  # First generate IDs
  nodes = Nodes()
  for idx, (ip, port) in enumerate(proposers + acceptors + learners):
    ip = ip.encode("utf-8")

    if [ip, port] in acceptors:
      kind = "acceptor"
    elif [ip, port] in proposers:
      kind = "proposer"
    elif [ip, port] in learners:
      kind = "learner"

    nodes[idx+1] = (ip, port, kind)

  P = []
  for ip, port in proposers:
    P.append(Proposer(nodes.get_id((ip, port)), nodes, ip, port))

  A = []
  for ip, port in acceptors:
    A.append(Acceptor(nodes.get_id((ip, port)), nodes, ip, port))

  L = []
  for ip, port in learners:
    P.append(Learner(nodes.get_id((ip, port)), nodes, ip, port))

  paxos = Paxos(nodes, A, P, L)
  try:
    paxos.start()
    paxos.leader_loop()
  except Exception, e:
    log.exception(e)
    paxos.stop()
