from paxos import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, ip='', port=0, proposers=[], learners=[]):
    PaxosRole.__init__(self, "Acceptor", ip, port)
    self.proposers = proposers # (ip, port) of proposers
    self.learners = learners # (ip, port) of learners
    self.rnd = 0 # Current round number
    self.vrnd = None # Last voted round number
    self.vval = None # Value of last voted round

  def __repr__(self):
    """Returns a string representation of this object, used when printing
    it."""
    return "<{0} {1}:{2} rnd={3} vrnd={4} vval={5}>".format(
      self.name, self.udp.ip, self.udp.port,
      self.rnd, self.vrnd, self.vval)

  # Phase 1b
  def on_prepare(self, c, n): # c = sender
    """Called when we receive a prepare message."""
    if n > self.rnd:
      self.rnd = n # the next round number
      log.info("{0} on_prepare({1}, {2})".format(self, c, n))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(c, self.rnd, self.vrnd, self.vval)
    else:
      log.info("{0} on_prepare({1}, {2}) but n<=self.rnd".format(self, c, n))

  # Phase 2b
  def on_accept(self, c, n, v): # c = sender
    """Called when we receive an accept message."""
    log.info("{0} on_accept({1}, {2}, {3})".format(self, c, n, v))

    if n >= self.rnd and n != self.vrnd:
      self.rnd = n
      self.vrnd = n
      self.vval = v

      # Send LEARN message to learners
      for L in self.learners:
        self.learn(L, n, v)

if __name__ == "__main__":
  try:
    a = Acceptor()
    a.loop()
  except KeyboardInterrupt:
    pass
