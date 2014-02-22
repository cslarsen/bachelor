from paxos import PaxosRole
import log

class Learner(PaxosRole):
  """A learner role."""
  def __init__(self, id, nodes, ip='', port=0):
    self.id = id
    self.nodes = nodes
    self.values = {} # learned values
    self._ip = ip
    self._port = port

  def setup(self):
    PaxosRole.__init__(self, "Learner", self._ip, self._port)
    self.loop()

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

