"""
Straight-forward implementation of Paxos taken from

    http://pdos.csail.mit.edu/6.824-2007/labs/lab-8.html

The idea is to

    * Create a (1) correct and (2) simple implementation of Paxos
    * Create a set of unit tests that will check that this works in edge
      cases and in face of other difficulties (nodes going down, etc).
    * For this we just simulate sending and receiving
    * When all tests pass and the algorithm looks good, we'll implement it
      as a POX-controller.

See also

    http://www.seas.harvard.edu/hc3/prize1/problems/paxos/paxos.txt
    http://www.seas.harvard.edu/hc3/prize1/problems/paxos/paxos_theorem.txt

Good ideas on testing edge cases

    http://pdos.csail.mit.edu/6.824-2005/handouts/l15.txt

Copyright (C) 2014 Christian Stigen Larsen
See README.md for licensing
"""

import pickle
import random
import sys
import time

NUM_NODES = 4
NODES = []

class Node(object):
  """A network node that has a name and can communicate to other Nodes.

  It understands messages that are prepended by a header, and can dispatch
  incoming messages to registered handlers.
  """
  NODES = []

  def __init__(self, id):
    self.id = id
    self.dispatch = {}

  def send(self, to, header, data):
    if to in NODES:
      self.log("Send {} to {}: {}".format(header, to, data))
      to.recv(to, pickle.dumps((header, data)))
    else:
      self.log("WARN: Cannot send to unknown node {}".format(to))

  def recv(self, sender, data):
    header, message = pickle.loads(data)
    if header in self.dispatch:
      for handler in self.dispatch[header]:
        handler(sender, message)
    else:
      self.log("WARN: No {} handler from {}: {}".format(header, sender, data))

  def add_handler(self, header, handler):
    """Register a handler. Can register several handlers for each header."""
    if not header in self.dispatch:
      self.dispatch[header] = []
    self.dispatch[header].append(handler)

  def log(self, msg):
    """Poor man's logger."""
    print("{}: {}".format(self, msg))

  def __repr__(self):
    return "node-{}".format(self.id)

class PaxosNode(Node):
  """A Paxos node."""
  def __init__(self, id, initial_contact):
    Node.__init__(self, id)

    # higheset value which node has accepted
    self.n_a = 0

    # highest proposal number which node has accepted
    self.v_a = 0

    # the highest proposal number seen in a prepare
    self.n_h = 0

    # the last proposal number the node has used in this round of paxos
    self.my_n = 0

    # highest view number we have accepted
    self.vid_h = 0

    # map of past view numbers to values
    self.views = {}

    # leader says agreement was reached, we can start new view
    self.done = False

    # the reffed algo mentioned some init contact, so adds its ups
    self.initial_contact = initial_contact

    self.leader = False

    # need this?
    self.prepareres_count = 0

    self.initialize_state()

    # Set up dispatch table
    dispatch = {
      "oldview":    self.on_oldview,
      "prepare":    self.on_prepare,
      "prepareres": self.on_prepareres,
      "reject":     self.on_reject,
      }
    for header, handler in dispatch.items():
      self.add_handler(header, handler)

  def initialize_state(self):
    """Should be called on each view change."""
    self.n_a = 0
    self.n_h = 0
    self.my_n = 0
    self.v_a = {}

  def on_oldview(self, sender, data):
    self.log("Got oldview from {}: {}".format(sender, data))
    if self.leader:
      vid, v = data
      self.views[vid] = v
      self.vid_h = vid
      self.view_change()
      self.restart_paxos()

  def on_prepareres(self, sender, data):
    self.prepareres_count += 1
    self.log("Got prepareres from {} (count is {}): {}".
      format(sender, self.prepareres_count, data))

    # majority? this is broken and wrong...
    # if leader gets prepareres from majority of nodes in views[vid_h]
    if self.prepareres_count > len(NODES)//2:
      pass

  def on_reject(self, sender, data):
    self.log("Got reject from {}: {}".format(sender, data))
    if self.leader:
      self.delay()
      self.restart_paxos()

  def view_change(self):
    self.log("view_change()")
    pass

  def restart_paxos(self):
    self.log("restart_paxos()")
    self.initialize_state()
    pass

  def delay(self):
    secs = random.randrange(3)
    self.log("Sleeping %d secs ..." % secs)
    sys.stdout.flush()
    time.sleep(secs)

  def on_prepare(self, sender, data):
    self.log("Got prepare from {}: {}".format(sender, data))

    vid, n = data
    if vid <= self.vid_h:
      return self.send(sender, "oldview", (vid, self.get_views_node(vid)))
    elif n > self.n_h:
      self.n_h = n
      self.done = False
      return self.send(sender, "prepareres", (self.n_a, self.v_a))
    else:
      return self.send(sender, "reject", None)

  def become_leader(self):
    """Propose that we want to become a leader (PHASE 1)."""
    self.log("Decides to become leader ... ")

    # Append node id (unique proposal number)
    self.my_n = max(self.n_h, self.my_n)+1
    self.done = False

    # send prepare to all nodes in
    # {views[vid_h], initial contact node, itself}
    for node in [self.get_view_node(self.vid_h), self.initial_contact, self]:
      if node is not None:
        self.send(node, "prepare", (self.vid_h+1, self.my_n))

  def get_view_node(self, id):
    """Thin wrapper around self.views so we don't keyerr"""
    if id in self.views:
      return self.views[id]
    return None

  def __repr__(self):
    return "node-%s" % self.id

if __name__ == "__main__":
  # Set up some nodes (all nodes 'initial contact' is the first node)
  print("Creating %d nodes" % NUM_NODES)
  for id in range(NUM_NODES):
    # the first node is not "invited" by anyone (None), the others are
    # invited by the previous one... imagine that you have to know a node to
    # join the paxos network...
    initial_contact = NODES[-1] if len(NODES)>0 else None
    NODES.append(PaxosNode(id, initial_contact))

  # Pick a random node to become leader, cannot be the first node
  while True:
    wannabe = random.choice(NODES)
    if wannabe != NODES[0]: break

  # This should start some discussions and console activity
  wannabe.become_leader()
