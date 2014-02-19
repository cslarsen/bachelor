from communication import PaxosRole
import log

class Acceptor(PaxosRole):
  """A classic Paxos acceptor."""
  def __init__(self, ip='', port=0):
    PaxosRole.__init__(self, "Acceptor", ip, port)
    self.proposers = set()
    self.learners = set()
    self.rnd = 0 # current round number
    self.vrnd = None # last voted round number
    self.vval = None # value of laste voted round

  # Phase 1b
  def on_prepare(self, c, n): # c = sender
    log.info("on_prepare({}, {})".format(c, n))
    if n > self.rnd:
      self.rnd = n # the next round number
      self.promise(c, self.rnd, self.vrnd, self.vval)

  # Phase 2b
  def on_accept(self, c, n, v): # c = sender
    log.info("on_accept({}, {}, {})".format(c, n, v))
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
