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
    return "<{} id={} |values|={}>".format(
      self.name,
      self.id,
      len(self.values))

  def on_learn(self, sender, n, v):
    dst = self.id
    src = self.nodes.get_id(sender)

    # Have we learned this value before?
    if not n in self.values:
      log.info("{}<-{}: on_learn(id={}, n={}, v={}) on {}".format(
        dst, src, src, n, v, self))
      self.values[n] = v
    else:
      log.info(("{}<-{}: on_learn(id={}, n={}, v={}) on {} " + 
                "IGNORED b/c already learned to be v={}").
                format(dst, src, src, n, v, self, self.values[n]))

