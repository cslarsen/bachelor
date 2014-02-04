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

NUM_NODES = 4
NODES = []

class Node(object):
  """A Paxos node."""
  def __init__(self, id, initial_contact):
    self.id = id

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

  def log(self, msg):
    """Poor man's logger."""
    print("{}: {}".format(self, msg))

  def initialize_state(self):
    """Should be called on each view change."""
    self.n_a = 0
    self.n_h = 0
    self.my_n = 0
    self.v_a = {}

  def send(self, to_node, message):
    """Send a message to a node."""

    if to_node in NODES:
      self.log("Send to {}: {}".format(to_node, message))
      to_node.recv(self, pickle.dumps(message))
    else:
      self.log("Error: Could not send message to unknown node {}".
        format(to_node))

  def recv(self, sender, data):
    """Receive a message from a node."""
    message = pickle.loads(data)

    header, data = message

    if header == "prepare":
      self.on_prepare(sender, data)
    # TODO: add more clauses here ...
    else:
      self.log("Warning: Unknown message header from {}: {}".
        format(sender, message))

  def on_prepare(self, sender, data):
    self.log("Got prepare from {}: {}".
      format(sender, data))

    vid, n = data
    if vid <= self.vid_h:
      return self.send(sender, self.oldview(vid, self.get_views_node(vid)))
    elif n > self.n_h:
      self.n_h = n
      self.done = False
      return self.send(sender, self.prepareres(self.n_a, self.v_a))
    else:
      return self.send(sender, self.create_reject_message())

  def create_prepare_message(self):
    """Creates a prepare mesasge"""
    return ("prepare", (self.vid_h+1, self.my_n))

  def create_reject_message(self):
    return ("reject")

  def oldview(self, vid, node):
    return ("??oldview", (vid, node)) # TODO: fixme

  def prepareres(self, na, va):
    return ("??prepareres", (na, va)) # TODO: fixme

  def phase1_become_leader(self):
    """We want to become a leader."""
    self.log("Decides to become leader ... ")

    # Append node id (unique proposal number)
    self.my_n = max(self.n_h, self.my_n)+1
    self.done = False

    # send prepare to all nodes in
    # {views[vid_h], initial contact node, itself}
    prepare_message = self.create_prepare_message()

    for node in [self.get_view_node(self.vid_h), self.initial_contact, self]:
      if node is not None:
        self.send(node, prepare_message)

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
    NODES.append(Node(id, initial_contact))

  # Pick a random node to become leader, cannot be the first node
  while True:
    wannabe = random.choice(NODES)
    if wannabe != NODES[0]: break

  # This should start some discussions and console activity
  wannabe.phase1_become_leader()
