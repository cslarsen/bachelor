from log import log

def launch():
  """Starts the controller."""
  from controller import SimplifiedPaxosController
  from pox.core import core
  logger = core.getLogger()

  def start_controller(event):
    logger.debug("Simplified Paxos controlling {}".format(event.connection))
    SimplifiedPaxosController(event.connection)

  core.openflow.addListenerByName("ConnectionUp", start_controller)