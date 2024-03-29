"""
Contains a simplified Paxos POX-controller.
"""

import pickle

from pox.core import core
#from pox.lib.revent import EventHalt, EventHaltAndRemove
from pox.lib.util import dpid_to_str
#import pox.forwarding.l2_learning as l2l
#import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from paxos import message
#from paxos import Paxos

class LearningSwitch(object):
  """A simple switch that learns which ports MAC addresses are connected
  to."""
  def __init__(self, connection, priority):
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
    self.log.info("Installing flow for %s.%i -> %s.%i" %
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


class SimplifiedPaxosController(object):
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

    # Highest priority; we get the events first
    connection.addListeners(self, priority=2)

    # Set name for our logger
    self.log = core.getLogger("Controller-{}".format(connection.ID))
    self.log.info("Launched controller on connection {}".format(connection.ID))

    # Lower priority; gets events after us
    self.subcontroller = LearningSwitch(connection, priority=1)

  def _handle_PacketIn(self, event):
    """Handles packets from the switches."""

    # Fetch the parsed packet
    packet = event.parsed

    if not packet.parsed:
      self.log.warning("{} -> {} Ignoring incomplete packet from event {}".format(
        self.getsrc(packet), self.getdst(packet), event))
      return

    # Fetch the raw packet
    packet_in = event.ofp

    if self.is_app_message(packet):
      return self.handle_app_message(event, packet, packet_in)

    if self.is_paxos_message(packet):
      return self.handle_paxos_message(packet, packet_in)

  def is_paxos_message(self, packet):
    """TODO: Implement."""
    udp = packet.find("udp")
    if udp:
      return message.paxos.isrecognized(udp.payload)
    else:
      return False

  def getsrc(self, packet):
    udp = packet.find("udp")
    ip = packet.find("ipv4")
    return "{}:{}".format(ip.srcip, udp.srcport)

  def getdst(self, packet):
    udp = packet.find("udp")
    ip = packet.find("ipv4")
    return "{}:{}".format(ip.dstip, udp.dstport)

  def handle_app_message(self, event, packet, packet_in):
    udp = packet.find("udp")
    #ip = packet.find("ipv4")

    raw = pickle.loads(udp.payload)
    msg = message.app.unmarshal(udp.payload)

    if len(msg) < 2:
      self.log.warning("Could not unmarshal app-level message: {}".format(raw))
      return
    command, args = msg

    src = self.getsrc(packet)
    dst = self.getdst(packet)

    self.log.info("{} -> {}: Received app-level message: {}".format(src, dst, raw))

  def handle_paxos_message(self, packet, packet_in):
    udp = packet.find("udp")
    raw = pickle.loads(udp.payload)
    msg = message.paxos.unmarshal(udp.payload)
    command, args = msg

    src = self.getsrc(packet)
    dst = self.getdst(packet)

    self.log.info("{} -> {}: Received Paxos message: {}".format(src, dst, raw))

  def is_app_message(self, packet):
    # Is this an UDP message?
    udp = packet.find("udp")
    if udp:
      return message.app.isrecognized(udp.payload)
    else:
      return False

def launch():
  """Starts the controller."""
  from controller import SimplifiedPaxosController
  from pox.core import core
  logger = core.getLogger()

  def start_controller(event):
    logger.info("Controlling conID={}, dpid={}".
        format(event.connection.ID, dpid_to_str(event.dpid)))
    SimplifiedPaxosController(event.connection)

  logger.info("This Nexus only sends {} bytes of each packet to the controllers".
      format(core.openflow.miss_send_len))
  core.openflow.addListenerByName("ConnectionUp", start_controller)
