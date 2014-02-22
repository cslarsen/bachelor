from paxos import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, id, nodes, ip='', port=0):
    PaxosRole.__init__(self, "Acceptor", ip, port)
    self.id = id
    self.nodes = nodes
    self.rnd = 0 # Current round number
    self.vrnd = None # Last voted round number
    self.vval = None # Value of last voted round

  def __repr__(self):
    """Returns a string representation of this object, used when printing
    it."""
    return "<{0} id={6} {1}:{2} rnd={3} vrnd={4} vval={5}>".format(
      self.name, self.udp.ip, self.udp.port,
      self.rnd, self.vrnd, self.vval, self.id)

  # Phase 1b
  def on_prepare(self, c, n): # c = sender
    """Called when we receive a prepare message."""
    if n > self.rnd:
      self.rnd = n # the next round number
      log.info("on_prepare({}, {}) on {}".format(c, n, self))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(c, self.rnd, self.vrnd, self.vval)
    else:
      log.info("IGNORED on_prepare({}, {}) on {} " +
               "but n={} <= self.rnd={}".format(c, n, self, n, self.rnd))

  # Phase 2b
  def on_accept(self, c, n, v): # c = sender
    """Called when we receive an accept message."""

    if n >= self.rnd and n != self.vrnd:
      self.rnd = n
      self.vrnd = n
      self.vval = v

      log.info("on_accept({}, {}, {}) on {}".format(c, n, v, self))

      # Send LEARN message to learners
      log.info("--- Sending LEARN to all from {} ---".format(self))
      for L in self.nodes.learners:
        self.learn(L, n, v)
    else:
      log.info("IGNORED on_accept({}, {}, {}) on {}".format(c, n, v, self))

if __name__ == "__main__":
  try:
    a = Acceptor()
    a.loop()
  except KeyboardInterrupt:
    pass
