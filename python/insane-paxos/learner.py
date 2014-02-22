from paxos import PaxosRole
import log

class Learner(PaxosRole):
  """A learner role."""
  def __init__(self, id, nodes, ip='', port=0):
    PaxosRole.__init__(self, "Learner", ip, port)
    self.id = id
    self.nodes = nodes

  def __repr__(self):
    return "<{} id={} {}:{}>".format(self.name, self.id, self.udp.ip,
        self.udp.port)

  def on_learn(self, sender, n, v):
    log.info("on_learn({}, {}, {}) on {}".format(sender, n, v, self))
