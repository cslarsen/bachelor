# -*- encoding: utf-8 -*-

import json
import multiprocessing as mp
import socket
import sys
import time
import uuid

from node import Node
import log

def trap_sigint(signum, frame):
  raise KeyboardInterrupt()

def json_load(filename):
  """Parse a JSON file and return result."""
  with open(filename, "rt") as f:
    return json.loads("\n".join(f.readlines()))

class Paxos(object):
  """A set of Paxos agents."""
  def __init__(self, node_addresses):
    self.addrs = {}
    for id, (ip, port) in enumerate(node_addresses):
      self.addrs[id+1] = (ip, port)

    self.client = Node("Ω", self.addrs)
    self.client.setup(loop=False)

    self.nodes = {}
    for id, (ip, port) in enumerate(node_addresses):
      self.nodes[id+1] = Node(id+1,
                              self.addrs,
                              self.client.address,
                              ip,
                              port)

    self.leader = self.nodes[1]

    # Set up one process per node
    self.procs = [mp.Process(target=n.setup) for n in self.nodes.values()]

  def start(self):
    """Starts all procs and waits until all agents are in the receive
    loop."""

    log.info("Starting {} node processes".format(len(self.procs)))
    [n.start() for n in self.procs]

    log.info("Leader has id={}".format(self.leader.id))

    log.info("Waiting until all nodes are up")
    for node in self.nodes.values():
      cookie = uuid.uuid4().hex
      while True:
        try:
          self.client.ping((node._ip, node._port), cookie)
          reply = self.client.pump()
          if reply == ("ping-reply", cookie):
            log.debug("Ω<-{} on_ping(id={}, cookie={})".format(
              node.id, node.id, cookie))
            break
        except socket.timeout:
          sys.stdout.write("z")
          sys.stdout.flush()
        except KeyboardInterrupt:
          return

  def stop(self):
    """Tell all agents to stop and join the processes."""
    log.info("Stopping {0} processes".format(len(self.procs)))

    # Tell objects to stop looping
    for node in self.nodes.values():
      self.client.shutdown((node._ip, node._port))

    # Wait for them to finish
    for proc in self.procs:
      if proc.is_alive():
        proc.join()
        proc.terminate()

  def loop(self):
    """Start leader loop."""
    value = 5
    self.client.trust_value((self.leader._ip, self.leader._port),
                            self.leader.id,
                            value)

    # TODO: Loop here until an Paxos instance has finished.
    while True:
      try:
        time.sleep(1)
        sys.stdout.write("x")
        sys.stdout.flush()
      except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        return

if __name__ == "__main__":
  config = json_load("config.json")
  paxos = Paxos(config["nodes"])

  try:
    paxos.start()
    paxos.loop()
  except Exception, e:
    log.exception(e)
  finally:
    paxos.stop()
