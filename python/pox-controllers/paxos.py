"""
Simple Paxos implemented entirely on a POX-controller.

Copyright (C) 2014 Christian Stigen Larsen
See README.md for licensing information.

To start, start Mininet using a remote controller:

    $ sudo mn --topo single,3 --switch ovsk --controller remote
                                                         ^^^^^^

and then start the Paxos POX controller, verifying that it announces itself
in the log:

    ./pox log.level --DEBUG path.to.paxos

where ``path.to.paxos`` should be a subdirectory from the POX directory that
holds this file.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class Paxos(object):
  """A simple Paxos controller."""
  def __init__(self, connection):
    self.connection = connection
    connection.addListeners(self)

  def resend_packet(self, packet_in, out_port, write_log=True):
    """Send packet to given output port."""
    msg = of.ofp_packet_out()
    msg.data = packet_in
    msg.actions.append(of.ofp_action_output(port = out_port))

    if write_log:
      log.debug("Resending packet {} to port {}".
        format(packet_in, out_port))

    self.connection.send(msg)

  def broadcast_packet(self, packet_in):
    """Broadcast packet to all nodes."""
    log.info("Broadcasting packet {}".format(packet_in))
    self.resend_packet(packet_in, of.OFPP_ALL, write_log=False)

  def hub(self, packet, packet_in):
    """A crude hub that broadcasts all incoming packets."""
    self.broadcast_packet(packet_in, of.OFPP_ALL)

  def _handle_PacketIn (self, event):
    """Handles packet in messages from the switch."""

    log.debug("Got event {}".format(event))

    # The parsed packet data
    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring incomplete packet from event {}".format(event))
      return

    # The actual ofp_packet_in message that caused packet to be sent to this
    # controller
    packet_in = event.ofp
    log.debug("Got packet {}".format(packet))
    log.debug("Got packet_in {}".format(packet_in))

    # For now, act like a hub
    self.hub(packet, packet_in)

def launch():
  """Starts the controller."""
  def start_switch(event):
    log.debug("Paxos controlling {}".format(event.connection))
    Paxos(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
