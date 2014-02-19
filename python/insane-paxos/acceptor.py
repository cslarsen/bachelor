from paxos import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, ip='', port=0, proposers=[], learners=[]):
    PaxosRole.__init__(self, "Acceptor", ip, port)
    self.proposers = proposers
    self.learners = learners
    self.rnd = 0 # current round number
    self.vrnd = None # last voted round number
    self.vval = None # value of laste voted round

  def __repr__(self):
    return "<{} {}:{} rnd={} vrnd={} vval={}>".format(
      self.name, self.udp.ip, self.udp.port,
      self.rnd, self.vrnd, self.vval)

  # Phase 1b
  def on_prepare(self, c, n): # c = sender
    log.info("Acceptor {} on_prepare({}, {})".format(
      self.udp.address, c, n))

    if n > self.rnd:
      self.rnd = n # the next round number
      self.promise(c, self.rnd, self.vrnd, self.vval)

  # Phase 2b
  def on_accept(self, c, n, v): # c = sender
    log.info("Acceptor {} on_accept({}, {}, {})".format(
      self.udp.address, c, n, v))

    if n >= self.rnd and n != self.vrnd:
      self.rnd = n
      self.vrnd = n
      self.vval = v

      for L in self.learners:
        self.learn(L, n, v)

if __name__ == "__main__":
  try:
    a = Acceptor()
    a.loop()
  except KeyboardInterrupt:
    pass
