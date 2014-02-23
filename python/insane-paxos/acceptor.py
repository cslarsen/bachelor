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

  def learn(self, to, rnd, vval):
    """Override to produce nicer log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: learn(rnd={}, vval={})".format(
      src, dst, rnd, vval))
    return PaxosRole.learn(self, to, rnd, vval)

  # Phase 1b
  def on_prepare(self, sender, crnd):
    """Called when we receive a prepare message."""
    src = self.nodes.get_id(sender)
    dst = self.id

    if crnd > self.rnd:
      self.rnd = crnd # the next round number
      log.info("{}<-{}: on_prepare(id={}, crnd={}) on {}".format(
        dst, src, src, crnd, self))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(sender, self.rnd, self.vrnd, self.vval)
    else:
      log.info(("{}<-{}: on_prepare(id={}, crnd={}) on {} " +
               "IGNORED b/c n <= self.rnd={}").format(
                 dst, src, src, crnd, self, crnd, self.rnd))

  # Phase 2b
  def on_accept(self, sender, crnd, vval):
    """Called when we receive an accept message."""
    src = self.nodes.get_id(sender)
    dst = self.id

    if crnd >= self.rnd and crnd != self.vrnd:
      self.rnd = crnd
      self.vrnd = crnd
      self.vval = vval

      log.info("{}<-{}: on_accept(id={}, crnd={}, vval={}) on {}".format(
        dst, src, src, crnd, vval, self))

      # Send LEARN message to learners
      log.info("Sending LEARN to all from {}".format(self.id))

      for learner in self.nodes.learners:
        self.learn(learner, crnd, vval)
    else:
      log.info(("{}<-{}: on_accept(id={}, crnd={}, vval={}) on {} " +
               "IGNORED b/c !(crnd>=rnd && crnd!=vrnd)").format(
                 dst, src, src, crnd, vval, self))
