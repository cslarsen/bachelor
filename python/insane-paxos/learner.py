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

  def on_learn(self, sender, rnd, vval):
    dst = self.id
    src = self.nodes.get_id(sender)

    # Have we learned this value before?
    if not rnd in self.values:
      log.info("{}<-{}: on_learn(id={}, rnd={}, vval={}) on {}".format(
        dst, src, src, rnd, vval, self))
      self.values[rnd] = vval
    else:
      log.info(("{}<-{}: on_learn(id={}, rnd={}, vval={}) on {} " + 
                "IGNORED b/c already learned to be v={}").
                format(dst, src, src, rnd, vval, self, self.values[rnd]))

