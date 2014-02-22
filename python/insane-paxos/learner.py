from paxos import PaxosRole
import log

class Learner(PaxosRole):
  """A learner role."""
  def __init__(self, id, nodes, ip='', port=0):
    PaxosRole.__init__(self, "Learner", ip, port)
    self.id = id
    self.nodes = nodes
    self.values = {} # learned values

  def __repr__(self):
    return "<{} {} {}:{}>".format(
      self.name,
      self.id,
      self.transport.ip,
      self.transport.port)

  def on_learn(self, sender, n, v):
    a = self.nodes.get_id(sender)

    # Have we learned this value before?
    if not n in self.values:
      log.info("< on_learn(id={}, n={}, v={}) on {}".format(a, n, v, self))
      self.values[n] = v
    else:
      log.info(("< on_learn(id={}, n={}, v={}) on {} " + 
                "IGNORED b/c already learned to be v={}").
                format(a, n, v, self, self.values[n]))

