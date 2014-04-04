import pox.core

paxos_leader = None
def propose_paxos_leader(paxos):
  """Designate the first Paxos instance as leader."""
  global paxos_leader
  if paxos_leader is None:
    paxos_leader = paxos
    paxos.isleader = True

class Paxos(object):
  """A simplified Paxos class that only performs ACCEPT and LEARN."""

  def __init__(self, connection):
    self.connection = connection
    self.rnd = 0 # current round number
    self.vrnd = None # last voted round number
    self.vval = None # value of last voted round
    self.learned_rounds = set()
    self.isleader = False
    self.log = pox.core.getLogger("Paxos-{}".format(self.connection.ID))

    propose_paxos_leader(self)
    if self.isleader:
      self.log.info("** We've been designated as a Paxos LEADER **")
    else:
      self.log.info("** We've been designated as a Paxos SLAVE **")

  # Phase 2b
  def on_accept(self, sender, crnd, vval):
    """Called when we receive an accept message."""
    if crnd >= self.rnd and crnd != self.vrnd:
      self.rnd = crnd
      self.vrnd = crnd
      self.vval = vval

      self.log.info("Paxos on_accept(crnd={}, vval={})".format(crnd, vval))

      # Send LEARN message to learners
      self.log.info("Sending LEARN to all from {}".format(self.id))

      # TODO: Implement LEARN here to all end-systems...
      # (all hosts except clients)
      #for address in self.nodes.values():
      #  self.learn(address, crnd, vval)
    else:
      self.log.warn(("Paxos on_accept(crnd={}, vval={}) " +
                "IGNORED: !(crnd>=rnd && crnd!=vrnd)").format(
                 crnd, vval))

  def on_learn(self, sender, rnd, vval):
    # Have we learned this value before?
    if not rnd in self.learned_rounds:
      self.log.info("on_learn(rnd={}, vval={})".format(rnd, vval))
      self.learned_rounds.update([rnd])
    else:
      self.log.warn(("on_learn(rnd={}, vval={}) " + 
                "IGNORED: already know rnd={}").
                  format(rnd, vval, rnd))
