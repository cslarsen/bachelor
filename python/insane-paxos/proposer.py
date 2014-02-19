from paxos import PaxosRole
import log

class Proposer(PaxosRole):
  """A classis Paxos proposer."""
  def __init__(self, ip='', port=0, acceptors=[]):
    PaxosRole.__init__(self, "Proposer", ip, port)
    self.acceptors = acceptors # A
    self.crnd = 0 # crnd
    self.mv = set() # MV

  def pickNext(self, crnd):
    """Selects proposal number larger than crnd."""
    # TODO: Is this correct? should we add by number of proposers to make it
    # unique?
    return crnd+1

  # Phase 1a
  def on_trust(self, sender, c):
    log.info("Proposer {} on_trust({}, {})".format(self.udp.address, sender, c))
    self.crnd = self.pickNext(self.crnd)
    self.mv = set()
    for acceptor in self.acceptors:
      self.prepare(acceptor, self.crnd)

  def on_unknown(self, sender, message):
    """Called when we didn't understand the message command."""
    log.warn("Proposer {} Unknown command from {}: '{}'".format(
      self.udp.address, sender, message))

  # Phase 2a
  def on_promise(self, sender, rnd, vrnd, vval):
    log.info("Proposer {} on_promise({}, {}, {}, {})".format(
      self.udp.address, sender, rnd, vrnd, vval))

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
      # TODO: Is this correct? we pick ANY of the values we have?
      # or can we here choose any NEW value?
      return 112233
      #i = random.randint(0, len(self.mv))
      #_, vval = self.mv[i]
      #return vval

    def pickLargest(mv):
      """Returns proposed value vval with largest vrnd."""
      _, vval = sorted(mv)[0]
      return vval

    if self.crnd == rnd:
      self.mv.append((vrnd, vval)) # add value of acceptor a

      if all_promises():
        if no_promises_with_value():
          cval = pickAny() # propose any value
        else:
          # pick proposed vval with largest vrnd
          cval = pickLargest(self.mv)

        for acceptor in self.acceptors:
          self.accept(acceptor, self.crnd, cval)

if __name__ == "__main__":
  try:
    p = Proposer(port=1234)
    p.loop()
  except KeyboardInterrupt:
    pass
