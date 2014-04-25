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

    # Defaults
    self.idle_timeout = 3600
    self.hard_timeout = 3600

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
      self.add_rule(mac, port)

  def add_rule(self, mac, port):
    self.log.info("Adding flow entry: If dest MAC is %s forward to port %i" % (mac, port))
    msg = of.ofp_flow_mod()

    # Previously: Match on as many fields as possible (from L2 POX example)
    #msg.match = of.ofp_match.from_packet(packet, event.port)
    # Now: Only match on destination port
    #msg.match = of.ofp_match()
    # Match on given destination MAC address
    msg.match.dl_dst = mac

    # Set entry timeouts
    msg.idle_timeout = self.idle_timeout
    msg.hard_timeout = self.hard_timeout

    # Action is to forward to given port
    msg.actions.append(of.ofp_action_output(port=port))

    self.connection.send(msg)

  def _handle_PacketIn(self, event):
    packet_in = event.ofp
    packet = event.parsed

    # Learn which port the sender is connected to and add rule
    self.learn_port(packet.src, event.port)

    # If we don't know the destination port yet, broadcast packet
    if not packet.dst in self.macports:
      self.log.debug("Don't know which port %s is on, rebroadcasting" % packet.dst)
      self.broadcast(packet_in)

def launch():
  """Starts the controller."""
  from pox.core import core
  logger = core.getLogger()

  def start_controller(event):
    logger.info("Controlling connection id {}, DPID {}".
        format(event.connection.ID, dpid_to_str(event.dpid)))
    c = BaselineController(event.connection)
    logger.info("Flow entry idle timeout is %d seconds" % c.idle_timeout)
    logger.info("Flow entry hard timeout is %d seconds" % c.hard_timeout)

  logger.info("*** Started BASELINE controller ***")
  logger.info("This Nexus only sends {} bytes of each packet to the controllers".
      format(core.openflow.miss_send_len))
  core.openflow.addListenerByName("ConnectionUp", start_controller)
