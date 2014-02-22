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
    PaxosRole.__init__(self, "Proposer", ip, port, get_id=nodes.get_id)
    self.id = id
    self.nodes = nodes
    self.crnd = None
    self.mv = set()
    self.v = None # The value we want to reach consensus for

  def __repr__(self):
    """Returns a string representation of this object."""
    return "<{} {} {}:{} crnd={} v={} |MV|={}>".format(
      self.name,
      self.id,
      self.transport.ip,
      self.transport.port,
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

  # Phase 1a
  # TODO: TRUST-messages should not go over the net, but as a func call.
  def on_trust(self, sender, c):
    """Called when we receive a TRUST message."""
    omega = self.nodes.get_id(sender)

    # Only act on TRUST meant for us
    if c == self.id:
      self.pickNext()
      self.mv = set()
      log.info("< on_trust(id={}, c={}) on {}".format(omega, c, self))
      for acceptor in self.nodes.acceptors:
        self.prepare(acceptor, self.crnd)
    else:
      log.info("< on_trust(id={}, c={}) on {} " +
               "IGNORED b/c c!=id".format(omega, c, self))

  def on_unknown(self, sender, message):
    """Called when we didn't understand the message command."""
    id = self.nodes.get_id(sender)
    log.warn("< on_unknown(id={}, message={}) on {} IGNORED".
      format(id, message, self))

  # Phase 2a
  def on_promise(self, sender, rnd, vrnd, vval):
    """Called when we receive a PROMISE message."""
    a = self.nodes.get_id(sender)

    def all_promises():
      """Got promises from all correct acceptors?"""
      f = ((len(self.nodes.acceptors))-1)/2 # TODO: Verify if correct
      return len(self.mv) >= f+1 # n=(2*f+1), n-t = f+1

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

      if all_promises():
        if no_promises_with_value():
          cval = pickAny() # propose any value
        else:
          # Pick proposed vval with largest vrnd.
          cval = pickLargest(self.mv)

        log.info("< on_promise(id={}, rnd={}, vrnd={}, vval={}) on {}".format(
          a, rnd, vrnd, vval, self))

        # Send ACCEPT message to ALL acceptors
        log.info("Sending ACCEPT to all from {}".format(self))
        for acceptor in self.nodes.acceptors:
          self.accept(acceptor, self.crnd, cval)
      else:
        log.info("< on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
          "IGNORED b/c !all_prom on {}".format(a, rnd, vrnd, vval, self))
    else:
      log.info("< on_promise(id={}, rnd={}, vrnd={}, vval={}) " +
        "IGNORED b/c crnd!=rnd on {}".format(a, rnd, vrnd, vval, self))
