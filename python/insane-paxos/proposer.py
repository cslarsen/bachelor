from paxos import PaxosRole
import log

class Proposer(PaxosRole):
  """A classis Paxos proposer."""
  def __init__(self, id, nodes, ip='', port=0):
    """
    Args:
      id:        A unique numerical ID for this node
      nodes:     A Nodes object
      ip:        IP-address to bind to, use default to get localhost.
      port:      Port to bind to, use default to get a random free port.
    """
    self.id = id
    self.nodes = nodes
    self._ip = ip
    self._port = port

  def setup(self, loop=True):
    PaxosRole.__init__(self, "Proposer", self._ip, self._port, get_id=self.nodes.get_id)
    self.crnd = None
    self.mv = set()
    self.v = None # The value we want to reach consensus for
    if loop:
      self.loop()

  def __repr__(self):
    """Returns a string representation of this object."""
    return "<{} id={} crnd={} v={} |MV|={}>".format(
      self.name,
      self.id,
      self.crnd,
      self.v,
      len(self.mv))

  def setvalue(self, value):
    """Set next value (payload) to attempt consensus on."""
    self.v = value
    log.info("Setting value v={} on {}".format(value, self))

  def pickNext(self):
    """Selects a new proposal number larger than crnd."""
    if self.crnd is None:
      self.crnd = self.id # first call to pickNext
    else:
      # Increment by number of nodes. Since each ID is unique, if everybody
      # increments with the number of nodes, each crnd will be unique. Also,
      # one can deduce the node id by taking `crnd % len(nodes)`.
      self.crnd += len(self.nodes)

  def ping(self, to, cookie):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.debug("{}->{}: ping(cookie={})".format(src, dst, cookie))
    return PaxosRole.ping(self, to, cookie)

  def trust(self, to, c):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: trust(c={})".format(src, dst, c))
    return PaxosRole.trust(self, to, c)

  def prepare(self, to, crnd):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: prepare(crnd={})".format(
      src, dst, crnd))
    return PaxosRole.prepare(self, to, crnd)

  def accept(self, to, crnd, cval):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.nodes.get_id(to)
    log.info("{}->{}: accept(crnd={}, cval={})".format(
      src, dst, crnd, cval))
    return PaxosRole.accept(self, to, crnd, cval)

  # Phase 1a
  # TODO: TRUST-messages should not go over the net, but as a func call.
  def on_trust(self, sender, c):
    """Called when we receive a TRUST message."""
    src = self.nodes.get_id(sender)
    dst = self.id
    omega = src

    # Only act on TRUST meant for us
    if c == self.id:
      self.pickNext()
      self.mv = set()
      log.info("{}<-{}: on_trust(id={}, c={}) on {}".format(
        dst, src, omega, c, self))

      log.info("Sending PREPARE to all from {}".format(self.id))

      for acceptor in self.nodes.acceptors:
        self.prepare(acceptor, self.crnd)
    else:
      log.info(("{}<-{}: on_trust(id={}, c={}) on {} " +
               "IGNORED b/c c!=id").format(
                 dst, src, omega, c, self))

  def on_unknown(self, sender, message):
    """Called when we didn't understand the message command."""
    dst = self.id
    src = self.nodes.get_id(sender)
    log.warn("{}<-{}: on_unknown(id={}, message={}) on {} IGNORED".
      format(dst, src, src, message, self))

  # Phase 2a
  def on_promise(self, sender, rnd, vrnd, vval):
    """Called when we receive a PROMISE message."""
    dst = self.id
    src = self.nodes.get_id(sender)
    a = src

    def f():
      """Return number of nodes that are allowed to fail."""
      return (len(self.nodes.acceptors)-1)/2 # TODO: Verify if correct

    def all_promises():
      """Got promises from all correct acceptors?"""
      return len(self.mv) >= f() + 1 # n=(2*f+1), t=f ==> n-t = f+1

    def enough_promises():
      """Same as all_promises, but fires as soon as we have a majority."""
      return len(self.mv) == f() + 1

    def no_promises_with_value():
      """No promises with a value?"""
      return all([vrnd is None for vrnd,_,_ in self.mv])

    def pickAny():
      """Returns the value we are proposing to be the next one we agree
      on."""
      return self.v

    def pickLargest(mv):
      """Returns proposed value vval with largest vrnd."""
      _, vval, _ = sorted(mv)[-1]
      return vval

    if self.crnd == rnd:
      # Add value of acceptor
      a = self.nodes.get_id(sender)
      self.mv.update([(vrnd, vval, a)])

      if enough_promises():
        if no_promises_with_value():
          cval = pickAny() # propose any value
        else:
          # Pick proposed vval with largest vrnd.
          cval = pickLargest(self.mv)

        log.info("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={}) on {}".format(
          dst, src, a, rnd, vrnd, vval, self))

        # Send ACCEPT message to ALL acceptors
        log.info("Sending ACCEPT to all from {}".format(self.id))

        for acceptor in self.nodes.acceptors:
          self.accept(acceptor, self.crnd, cval)
      else:
        log.info(("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
          "IGNORED b/c |MV|={}<{} on {}").format(
            dst, src, a, rnd, vrnd, vval, len(self.mv), f()+1, self))
    else:
      log.info(("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
        "IGNORED b/c crnd={} != rnd on {}").format(
          dst, src, a, rnd, vrnd, vval, self.crnd, self))
