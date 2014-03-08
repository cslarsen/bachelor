from pox.core import core

from paxos_controller import SimplifiedPaxosController

log = core.getLogger()

def launch():
  """Starts the controller."""
  def start_controller(event):
    log.debug("Simplified Paxos controlling {}".format(event.connection))
    SimplifiedPaxosController(event.connection)

  core.openflow.addListenerByName("ConnectionUp", start_controller)
