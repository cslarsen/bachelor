# -*- encoding: utf-8 -*-

from paxos import PaxosRole
import log

class Node(PaxosRole):
  """A Paxos node that takes ALL three roles: Proposer, Acceptor and
  Leaner."""
  def __init__(self, id, nodes, omega=None, ip='', port=0):
    self.id = id
    self._ip = ip
    self._port = port
    self.nodes = nodes
    self.values = {} # learned values
    self.omega = omega

    # Normalize 0.0.0.0
    if self.omega is not None:
      if self.omega[0] == "0.0.0.0":
        self.omega = ("127.0.0.1", self.omega[1])

    self.rnd = 0 # Current round number
    self.vrnd = None # Last voted round number
    self.vval = None # Value of last voted round
    self.crnd = None
    self.mv = set()
    self.v = None # The value we want to reach consensus for

  def get_id(self, sender):
    if sender == self.omega:
      return "Ω"

    for (node_id, node_address) in self.nodes.items():
      if node_address == sender:
        return node_id

    return "{}:{}".format(sender[0], sender[1])

  def setup(self, loop=True):
    """Instantiates parent to bind address in own process space."""
    PaxosRole.__init__(self, "Node", self._ip, self._port, self.get_id)
    if loop:
      self.loop()

  def __repr__(self):
    return "Node {}".format(self.id)

  def shutdown(self, to):
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: shutdown()".format(src, dst))
    return PaxosRole.shutdown(self, to)

  def trust_value(self, to, c, value):
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: trust_value(c={}, value={})".format(src, dst, c,
      value))
    return PaxosRole.trust_value(self, to, c, value)

  def promise(self, to, rnd, vrnd, vval):
    """Override promise to produce nicer log messages."""
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: promise(rnd={}, vrnd={}, vval={})".format(
      src, dst, rnd, vrnd, vval))
    return PaxosRole.promise(self, to, rnd, vrnd, vval)

  def learn(self, to, rnd, vval):
    """Override to produce nicer log messages."""
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: learn(rnd={}, vval={})".format(
      src, dst, rnd, vval))
    return PaxosRole.learn(self, to, rnd, vval)

  def on_trust_value(self, sender, c, value):
    src = self.get_id(sender)
    dst = self.id
    log.info("{}<-{}: on_trust_value(id={}, c={}, value={})".format(
      dst, src, src, c, value))
    self.setvalue(value)
    self.on_trust(sender, c)

  def on_shutdown(self, sender):
    src = self.get_id(sender)
    dst = self.id
    log.info("{}<-{}: on_shutdown(id={})".format(dst, src, src))
    self.stop = True

  # Phase 1b
  def on_prepare(self, sender, crnd):
    """Called when we receive a prepare message."""
    src = self.get_id(sender)
    dst = self.id

    if crnd > self.rnd:
      self.rnd = crnd # the next round number
      log.info("{}<-{}: on_prepare(id={}, crnd={})".format(
        dst, src, src, crnd))

      # Send PROMISE message back to the one who sent us a PREPARE message
      self.promise(sender, self.rnd, self.vrnd, self.vval)
    else:
      log.warn(("{}<-{}: on_prepare(id={}, crnd={}) " +
                "IGNORED: n <= self.rnd={}").format(
                 dst, src, src, crnd, crnd, self.rnd))

  # Phase 2b
  def on_accept(self, sender, crnd, vval):
    """Called when we receive an accept message."""
    src = self.get_id(sender)
    dst = self.id

    if crnd >= self.rnd and crnd != self.vrnd:
      self.rnd = crnd
      self.vrnd = crnd
      self.vval = vval

      log.info("{}<-{}: on_accept(id={}, crnd={}, vval={})".format(
        dst, src, src, crnd, vval))

      # Send LEARN message to learners
      log.info("Sending LEARN to all from {}".format(self.id))

      for address in self.nodes.values():
        self.learn(address, crnd, vval)
    else:
      log.warn(("{}<-{}: on_accept(id={}, crnd={}, vval={}) " +
                "IGNORED: !(crnd>=rnd && crnd!=vrnd)").format(
                 dst, src, src, crnd, vval))

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
    dst = self.get_id(to)
    log.debug("{}->{}: ping(cookie={})".format(src, dst, cookie))
    return PaxosRole.ping(self, to, cookie)

  def trust(self, to, c):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: trust(c={})".format(src, dst, c))
    return PaxosRole.trust(self, to, c)

  def prepare(self, to, crnd):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: prepare(crnd={})".format(
      src, dst, crnd))
    return PaxosRole.prepare(self, to, crnd)

  def accept(self, to, crnd, cval):
    """Override to produce nice log messages."""
    src = self.id
    dst = self.get_id(to)
    log.info("{}->{}: accept(crnd={}, cval={})".format(
      src, dst, crnd, cval))
    return PaxosRole.accept(self, to, crnd, cval)

  # Phase 1a
  # TODO: TRUST-messages should not go over the net, but as a func call.
  def on_trust(self, sender, c):
    """Called when we receive a TRUST message."""
    src = self.get_id(sender)
    dst = self.id
    omega = src

    # Only act on TRUST meant for us
    if c == self.id:
      self.pickNext()
      self.mv = set()
      log.info("{}<-{}: on_trust(id={}, c={})".format(dst, src, omega, c))

      # All nodes are also acceptors
      log.info("Sending PREPARE to all from {}".format(self.id))
      for address in self.nodes.values():
        self.prepare(address, self.crnd)
    else:
      log.warn("{}<-{}: on_trust(id={}, c={}) IGNORED: c!=id".
        format(dst, src, omega, c))

  def on_unknown(self, sender, message):
    """Called when we didn't understand the message command."""
    dst = self.id
    src = self.get_id(sender)
    log.warn("{}<-{}: on_unknown(id={}, message={}) IGNORED".
      format(dst, src, src, message))

  # Phase 2a
  def on_promise(self, sender, rnd, vrnd, vval):
    """Called when we receive a PROMISE message."""
    dst = self.id
    src = self.get_id(sender)
    a = src

    def failure_nodes():
      """Return number of nodes that are allowed to fail."""
      return (len(self.nodes)-1)/2 # TODO: Verify if correct

    def all_promises():
      """Got promises from all correct acceptors?"""
      return len(self.mv) >= failure_nodes() + 1 # n=(2*f+1), t=f ==> n-t = f+1

    def enough_promises():
      """Same as all_promises, but fires as soon as we have a majority."""
      return len(self.mv) == failure_nodes() + 1

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
      a = self.get_id(sender)
      self.mv.update([(vrnd, vval, a)])

      if enough_promises():
        if no_promises_with_value():
          cval = pickAny() # propose any value
        else:
          # Pick proposed vval with largest vrnd.
          cval = pickLargest(self.mv)

        log.info("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={})".
          format(dst, src, a, rnd, vrnd, vval))

        # Send ACCEPT message to ALL acceptors
        log.info("Sending ACCEPT to all from {}".format(self.id))

        for address in self.nodes.values():
          self.accept(address, self.crnd, cval)
      else:
        log.warn(("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
          "IGNORED: |MV|={} != {}").format(
            dst, src, a, rnd, vrnd, vval, len(self.mv), failure_nodes()+1))
    else:
      log.warn(("{}<-{}: on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
        "IGNORED: crnd={} != rnd").format(
          dst, src, a, rnd, vrnd, vval, self.crnd))

  def on_learn(self, sender, rnd, vval):
    dst = self.id
    src = self.get_id(sender)

    # Have we learned this value before?
    if not rnd in self.values:
      log.info("{}<-{}: on_learn(id={}, rnd={}, vval={})".format(
        dst, src, src, rnd, vval))
      self.values[rnd] = vval
    else:
      log.warn(("{}<-{}: on_learn(id={}, rnd={}, vval={}) " + 
                "IGNORED: already know rnd={}").
                  format(dst, src, src, rnd, vval, rnd))
