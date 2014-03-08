"""
Contains a simplified Paxos POX-controller.

Written by Christian Stigen Larsen

HOW TO LAUNCH:

    $ sudo mn --topo single,3 --switch ovsk --controller remote
                                                         ^^^^^^

  then start the Paxos POX controller, verifying that it announces itself in
  the log:

    ./pox log.level --DEBUG path.to.paxos

  where path.to.paxos should be a subdirectory from the POX-directory that
  holds this file.

ABOUT:

  This is not full Paxos! It only provides ACCEPT and LEARN messages, and
  this controller is the SOLE LEADER of the Paxos system.

  Aim: Show that by moving Paxos-functionality from the controller down to
  the OpenFlow-tables in the switches, we will achieve a performance gain
  compared to a system where Paxos is implemented in the nodes.

  We must also show that this performance gain would still be valid if we
  implemented the all of Paxos.

TODO:

  - find out how many switches there are
  - need to know how many nodes we have
  - need to route messages as hub/switch
  - need to be able to discern Paxos and client-messages

"""

from pox.core import core
import pox.openflow.libopenflow_01 as openflow

log = core.getLogger()

class PaxosController(object):
  """
  A simplified Paxos POX-controller that also works as a hub/switch.  Only
  handles ACCEPT and LEARN messages for Paxos and also application level
  messages between this controller and the clients and service nodes.

  A service node is a node connected to a switch, and which provides some
  service like e.g. a lock-server, a key-value store. A client is those who
  wnat to use the service.
  """

  def __init__(self, connection):
    self.connection = connection
    connection.addListeners(self)

  def _handle_PacketIn(self, event):
    """Handles packets from the switches."""
    log.debug("Got event {}".format(event))

    # Fetch the parsed packet data
    packet = event.parsed

    if not packet.parsed:
      log.warning("Ignoring incomplete packet from even {}".format(event))
      return
    else:
      log.debug("Got packet {}".format(packet))

    # Fetch the actual ofp__packet_in_message that caused packet to be sent
    # to this controller
    packet_in = event.ofp
    log.debug("Got packet_in {}".format(packet_in))

    if self.is_paxos_message(packet):
      self.handle_paxos_message(packet):
    elif self.is_client_message(packet):
      self.handle_client_message(packet):
    elif self.is_server_message(packet):
      self.handle_server_message(packet):
    else:
      # For now, act like a hub
      self.act_like_hub(packet, packet_in)

  def act_lke_hub(self, packet, packet_in):
    """A simple hub that broadcasts all incoming packets."""
    self.broadcast_packet(packet_in)

  def broadcast_packet(self, packet_in, 
    """Broadcast packet to all nodes."""
    log.info("Broadcasting packet {}".format(packet_in))
    port_send_to_all = openflow.OFPP_ALL
    self.resend_packet(packet-In, port_send_to_all)

  def resend_packet(self, packet_in, out_port):
    """Send packet to given output port."""
    msg = openflow.ofp_packet_out()
    msg.data = packet_in
    msg.actions.append(openflow.ofp_action_output(port = out_port))
    self.connection.send(msg)

  def is_paxos_message(self, packet):
    """TODO: Implement."""
    return False

  def is_client_message(self, packet):
    """TODO: Implement."""
    return False

  def is_server_message(self, packet):
    """TODO: Implement."""
    return False

def launch():
  """Starts the controller."""

  def start_controller(event):
    log.debug("Simplified Paxos controlling {}".format(event.connection))
    Paxos(event.connection)

  core.openflow.addListenerByName("ConnectionUp", start_controller)
