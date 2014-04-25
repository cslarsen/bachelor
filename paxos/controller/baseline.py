"""
An L2 learning switch.

We use this for benchmarking.

TODO: - Catch SIGINT and shut down gracefully.. if we do
          ssh mininet make bench-baseline-pox
        and CTRL+D, then the process will not stop, only the ssh connection
        will die (so we have to killall pox procs).
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

    # Map of MAC address to PORT
    self.macports = {}

    # Defaults
    self.idle_timeout = 3600
    self.hard_timeout = 3600

    # If set to true, log flow table misses
    self.log_misses = False

    # Log misses with a dot
    self.log_miss_as_dot = True

    self.log = core.getLogger("Switch-{}".format(connection.ID))
    self.log.info("----")
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))
    self.log.debug("idle timeout={}, hard timeout={}".format(
      self.idle_timeout, self.hard_timeout))
    self.log.info("----")

    # Listen for events from the switch
    connection.addListeners(self, priority=priority)

    # When connection goes down, we need to reset our MAC table
    connection.addListenerByName("ConnectionDown", self.connectionDown)

  def connectionDown(self, event):
    """Called when connection to switch goes down."""
    self.log.info("Connection to switch has gone down")
    self.clear_macports()
    self.clear_flowtable()

    # FUN FACT:
    # If mininet ping test starts and this controller stops, if we don't
    # clear out a fully populated flow table, then mininet's switch will
    # continue working because it can handle stuff on its own with its flow
    # table entries.

  def clear_macports(self):
    """Clears out learned MAC ports."""
    self.log.info("Clearing out MAC->PORT table (flushing {} entries)".
        format(len(self.macports)))
    self.macports = {}

  def clear_flowtable(self):
    """TODO: Remove all rules from the flow table."""
    pass

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
      if self.log_misses:
        self.log.debug("Don't know which port %s is on, rebroadcasting" % packet.dst)

      if self.log_miss_as_dot:
        sys.stdout.write("x")
        sys.stdout.flush()

      self.broadcast(packet_in)

def launch():
  """Starts the controller."""
  log = core.getLogger()
  Controller = BaselineController

  def start_controller(event):
    Controller(event.connection)

  log.info("** Using POX controller of type {} **".format(Controller.__name__))
  log.info("This nexus only sends the first {} bytes of each packet to the controllers".
      format(core.openflow.miss_send_len))

  # Listen to connection up events
  core.openflow.addListenerByName("ConnectionUp", start_controller)
