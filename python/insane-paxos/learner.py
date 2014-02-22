from paxos import PaxosRole
import log

class Learner(PaxosRole):
  """A learner role."""
  def __init__(self, id, nodes, ip='', port=0):
    PaxosRole.__init__(self, "Learner", ip, port)
    self.id = id
    self.nodes = nodes

  def __repr__(self):
    return "<{} {} {}:{}>".format(
      self.name,
      self.id,
      self.transport.ip,
      self.transport.port)

  def on_learn(self, sender, n, v):
    a = self.nodes.get_id(sender)
    log.info("< on_learn({}, {}, {}) on {}".format(a, n, v, self))
