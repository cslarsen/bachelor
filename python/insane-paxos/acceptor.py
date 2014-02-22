from paxos import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, id, nodes, ip='', port=0):
    PaxosRole.__init__(self, "Acceptor", ip, port, nodes.get_id)
    self.id = id
    self.nodes = nodes
    self.rnd = 0 # Current round number
    self.vrnd = None # Last voted round number
    self.vval = None # Value of last voted round

  def __repr__(self):
    """Returns a string representation of this object, used when printing
    it."""
    return "<{} {} {}:{} rnd={} vrnd={} vval={}>".format(
      self.name,
      self.id,
      self.transport.ip,
      self.transport.port,
      self.rnd,
      self.vrnd,
      self.vval)

  # Phase 1b
  def on_prepare(self, sender, n):
    """Called when we receive a prepare message."""
    c = self.nodes.get_id(sender)

    if n > self.rnd:
      self.rnd = n # the next round number
      log.info("< on_prepare(id={}, n={}) on {}".format(c, n, self))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(sender, self.rnd, self.vrnd, self.vval)
    else:
      log.info(("< on_prepare(id={}, n={}) on {} " +
               "IGNORED b/c n <= self.rnd={}").format(c, n, self, n, self.rnd))

  # Phase 2b
  def on_accept(self, sender, n, v):
    """Called when we receive an accept message."""
    c = self.nodes.get_id(sender)

    if n >= self.rnd and n != self.vrnd:
      self.rnd = n
      self.vrnd = n
      self.vval = v

      log.info("< on_accept(id={}, n={}, v={}) on {}".format(c, n, v, self))

      # Send LEARN message to learners
      log.info("Sending LEARN to all from {}".format(self.id))

      for L in self.nodes.learners:
        self.learn(L, n, v)
    else:
      log.info(("< on_accept(id={}, n={}, v={}) on {} " +
               "IGNORED b/c !(n>=rnd && n!=vrnd)").format(c, n, v, self))

if __name__ == "__main__":
  try:
    a = Acceptor()
    a.loop()
  except KeyboardInterrupt:
    pass
