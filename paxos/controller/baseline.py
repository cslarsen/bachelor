"""
Contains a simplified Paxos POX-controller.
"""

import pickle
import random
import sys

from pox.core import core
from pox.lib.revent import EventHalt, EventHaltAndRemove
from pox.lib.util import dpid_to_str
import pox.forwarding.l2_learning as l2l
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from paxos import message
from paxos import Paxos

class BaselineController(object):
  """A simple switch that learns which ports MAC addresses are connected
  to."""
  def __init__(self, connection, priority=1):
    self.connection = connection
    connection.addListeners(self, priority=priority)
    self.macports = {} # maps MAC address -> port
    self.log = core.getLogger("Switch-{}".format(connection.ID))

  def drop(self, event, packet):
    """Instructs switch to drop packet."""
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    self.connection.send(msg)

  def broadcast(self, packet_in):
    """Forward packet to all nodes."""
    self.forward(packet_in, of.OFPP_ALL)

  def forward(self, packet_in, port):
     """Instructs switch to forward the packet to the given port."""
     msg = of.ofp_packet_out()
     msg.data = packet_in
     msg.actions.append(of.ofp_action_output(port=port))
     self.connection.send(msg)

  def learn_port(self, mac, port):
    """Learns which port a MAC address is located."""
    if mac not in self.macports:
      self.macports[mac] = port
      self.log.info("MAC {} is on port {}".format(mac, port))

  def add_rule(self, event, packet, port, idle_timeout=10, hard_timeout=30):
    self.log.info("BaselinePOX: Installing flow for %s.%i -> %s.%i" %
              (packet.src, event.port, packet.dst, port))
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet, event.port)
    msg.idle_timeout = idle_timeout
    msg.hard_timeout = hard_timeout
    msg.actions.append(of.ofp_action_output(port = port))
    msg.data = event.ofp # 6a
    self.connection.send(msg)

  def _handle_PacketIn(self, event):
    packet_in = event.ofp
    packet = event.parsed

    # Learn which port the sender is connected to
    self.learn_port(packet.src, event.port)

    # Do we know the destination port as well?
    if packet.dst in self.macports:

      install_flows = True
      if install_flows:
        # Yes; forward to the port it's on
        #self.forward(packet_in, self.macports[packet.dst])
        self.add_rule(event, packet, self.macports[packet.dst], hard_timeout=10)
      else:
        # Add a rule for this and forward the first packet
        self.forward(packet_in, self.macports[packet.dst])

    else:
      # No; just forward it to everyone
      self.broadcast(packet_in)

def launch():
  """Starts the controller."""
  from pox.core import core
  logger = core.getLogger()

  def start_controller(event):
    logger.info("Controlling conID={}, dpid={}".
        format(event.connection.ID, dpid_to_str(event.dpid)))
    BaselineController(event.connection)

  logger.info("*** Started BASELINE controller ***")
  logger.info("This Nexus only sends {} bytes of each packet to the controllers".
      format(core.openflow.miss_send_len))
  core.openflow.addListenerByName("ConnectionUp", start_controller)
