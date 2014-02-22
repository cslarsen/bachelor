from paxos import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, id, nodes, ip='', port=0):
    self.id = id
    self._ip = ip
    self._port = port
    self.nodes = nodes

  def setup(self, loop=True):
    """Instantiates parent to bind address in own process space."""
    PaxosRole.__init__(self, "Acceptor", self._ip, self._port, self.nodes.get_id)
    self.rnd = 0 # Current round number
    self.vrnd = None # Last voted round number
    self.vval = None # Value of last voted round
    if loop:
      self.loop()

  def __repr__(self):
    """Returns a string representation of this object, used when printing
    it."""
    return "<{} id={} rnd={} vrnd={} vval={}>".format(
      self.name,
      self.id,
      self.rnd,
      self.vrnd,
      self.vval)

  def promise(self, to, rnd, vrnd, vval):
    """Override promise to produce nicer log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: promise(rnd={}, vrnd={}, vval={})".format(
      src, dst, rnd, vrnd, vval))
    return PaxosRole.promise(self, to, rnd, vrnd, vval)

  def learn(self, to, n, v):
    """Override to produce nicer log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: learn(n={}, v={})".format(
      src, dst, n, v))
    return PaxosRole.learn(self, to, n, v)

  # Phase 1b
  def on_prepare(self, sender, n):
    """Called when we receive a prepare message."""
    src = self.nodes.get_id(sender)
    dst = self.id
    c = src

    if n > self.rnd:
      self.rnd = n # the next round number
      log.info("{}<-{}: on_prepare(id={}, n={}) on {}".format(
        dst, src, c, n, self))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(sender, self.rnd, self.vrnd, self.vval)
    else:
      log.info(("{}<-{}: on_prepare(id={}, n={}) on {} " +
               "IGNORED b/c n <= self.rnd={}").format(
                 dst, src, c, n, self, n, self.rnd))

  # Phase 2b
  def on_accept(self, sender, n, v):
    """Called when we receive an accept message."""
    src = self.nodes.get_id(sender)
    dst = self.id
    c = src

    if n >= self.rnd and n != self.vrnd:
      self.rnd = n
      self.vrnd = n
      self.vval = v

      log.info("{}<-{}: on_accept(id={}, n={}, v={}) on {}".format(
        dst, src, c, n, v, self))

      # Send LEARN message to learners
      log.info("Sending LEARN to all from {}".format(self.id))

      for L in self.nodes.learners:
        self.learn(L, n, v)
    else:
      log.info(("{}<-{}: on_accept(id={}, n={}, v={}) on {} " +
               "IGNORED b/c !(n>=rnd && n!=vrnd)").format(
                 dst, src, c, n, v, self))
