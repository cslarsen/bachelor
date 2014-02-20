from paxos import PaxosRole
import log

class Proposer(PaxosRole):
  """A classis Paxos proposer."""
  def __init__(self, ip='', port=0, acceptors=[]):
    PaxosRole.__init__(self, "Proposer", ip, port)
    self.acceptors = acceptors
    self.crnd = 0
    self.mv = set()
    self.v = None

  def __repr__(self):
    """Returns a string representation of this object."""
    return "<{0} {1}:{2} crnd={3} v={4}>".format(
      self.name, self.udp.ip, self.udp.port,
      self.crnd, self.v)

  def pickNext(self, crnd):
    """Selects proposal number larger than crnd."""
    # TODO: Is this correct? should we add by number of proposers to make it
    # unique? i.e, if each agent has a unique number n, and we have m agents
    # in totalt, then we can create a system-wide unique round number by
    # setting crnd=n initially and then, below, incrementing with m (a trick
    # I saw in a Paxos implementation on github)
    return crnd+1

  # Phase 1a
  def on_trust(self, sender, c):
    """Called when we receive a TRUST message."""
    log.info("{0} on_trust({1}, {2})".format(self, sender, c))
    self.crnd = self.pickNext(self.crnd)
    self.mv = set()
    for acceptor in self.acceptors:
      self.prepare(acceptor, self.crnd)

  def on_unknown(self, sender, message):
    """Called when we didn't understand the message command."""
    log.warn("{0} on_unknown({1}, {2})".format(self, sender, message))

  # Phase 2a
  def on_promise(self, sender, rnd, vrnd, vval):
    """Called when we receive a PROMISE message."""
    log.info("{0} on_promise({1}, {2}, {3}, {4})".format(self,
      sender, rnd, vrnd, vval))

    def all_promises():
      """Got promises from all correct acceptors?"""
      # TODO: Vet ikke hva n_a og t_a er
      n_a = 0
      t_a = 0
      return len(self.mv) >= n_a - t_a

    def no_promises_with_value():
      """No promises with a value?"""
      return all([vrnd is None for vrnd,_ in self.mv])

    def pickAny():
      """Returns the value we are proposing to be the next one we agree
      on."""
      return self.v

    def pickLargest(mv):
      """Returns proposed value vval with largest vrnd."""
      _, vval = sorted(mv)[0]
      return vval

    if self.crnd == rnd:
      self.mv.update([(vrnd, vval)]) # add value of acceptor a

      if all_promises():
        if no_promises_with_value():
          cval = pickAny() # propose any value
        else:
          # pick proposed vval with largest vrnd
          cval = pickLargest(self.mv)

        # Send ACCEPT message to ALL acceptors
        for acceptor in self.acceptors:
          self.accept(acceptor, self.crnd, cval)
