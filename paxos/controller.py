"""
Contains a simplified Paxos POX-controller.

Written by Christian Stigen Larsen

HOW TO LAUNCH:

    $ sudo mn --topo single,3 --switch ovsk --controller remote
                                                         ^^^^^^

  then start the Paxos POX controller, verifying that it announces itself in
  the log:

    ./pox.py log.level --DEBUG path.to.paxos

  where path.to.paxos should be a subdirectory from the POX-directory that
  holds this file.

EASIER WAY TO START:

    $ ssh mininet
    $ cd paxos; make pox

    In other window
    $ ssh mininet
    $ cd paxos; sudo python test-client-ctrl.py

    Now try in mininet REPL:
    paxos/mininet> h1 python clients.py 10.0.0.1 1234

    Should detect a client message.

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

import pickle
import sys

from message import (paxos, client)

from pox.core import core
import pox.openflow.libopenflow_01 as openflow
import pox.lib.packet as pkt
import pox.forwarding.l2_learning as l2l

log = core.getLogger()

"""Set to ["event", "packet"] if you want to debug-log events and
messages."""
LOG_PACKETS = []

"""Same as LOG_PACKETS, but print dots instead of log message."""
LOG_PACKETS_DOT = []

class PaxosInstance(object):
  def __init__(self):
    self.rnd = 0 # current round number
    self.vrnd = None # last voted round number
    self.vval = None # value of last voted round
    self.learned_rounds = set()

  # Phase 2b
  def on_accept(self, sender, crnd, vval):
    """Called when we receive an accept message."""
    if crnd >= self.rnd and crnd != self.vrnd:
      self.rnd = crnd
      self.vrnd = crnd
      self.vval = vval

      log.info("Paxos on_accept(crnd={}, vval={})".format(crnd, vval))

      # Send LEARN message to learners
      log.info("Sending LEARN to all from {}".format(self.id))

      # TODO: Implement LEARN here to all end-systems...
      # (all hosts except clients)
      #for address in self.nodes.values():
      #  self.learn(address, crnd, vval)
    else:
      log.warn(("Paxos on_accept(crnd={}, vval={}) " +
                "IGNORED: !(crnd>=rnd && crnd!=vrnd)").format(
                 crnd, vval))

  def on_learn(self, sender, rnd, vval):
    # Have we learned this value before?
    if not rnd in self.learned_rounds:
      log.info("on_learn(rnd={}, vval={})".format(rnd, vval))
      self.learned_rounds.update([rnd])
    else:
      log.warn(("on_learn(rnd={}, vval={}) " + 
                "IGNORED: already know rnd={}").
                  format(rnd, vval, rnd))


class BroadcastHub(object):
  """A naive hub that broadcasts all packets."""
  def __init__(self, connection):
    self.connection = connection
    connection.addListeners(self, priority=5)

  def broadcast_packet(self, packet_in):
    """Broadcast packet to all nodes."""
    port_send_to_all = openflow.OFPP_ALL
    self.resend_packet(packet_in, port_send_to_all)

  def resend_packet(self, packet_in, out_port):
    """Send packet to given output port."""
    msg = openflow.ofp_packet_out()
    msg.data = packet_in
    msg.actions.append(openflow.ofp_action_output(port = out_port))
    self.connection.send(msg)

  def _handle_PacketIn(self, event):
    packet_in = event.ofp
    self.broadcast_packet(packet_in)


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
    connection.addListeners(self, priority=10) # call this handler first

    # Don't use the L2 learning switch, because it installs flow entries so
    # that subsequent packets will be routed directly, without us seeing
    # them.
    #self.switch = l2l.LearningSwitch(connection, False)
    self.switch = BroadcastHub(connection)

  def _handle_PacketIn(self, event):
    """Handles packets from the switches."""
    if "event" in LOG_PACKETS:
      log.debug("Got event {}".format(event))
    elif "event" in LOG_PACKETS_DOT:
      sys.stdout.write(".")
      sys.stdout.flush()

    # Fetch the parsed packet data
    packet = event.parsed

    if not packet.parsed:
      log.warning("{} -> {} Ignoring incomplete packet from event {}".format(
        self.getsrc(packet), self.getdst(packet), event))
      return
    else:
      if "packet" in LOG_PACKETS:
        log.debug("{} -> {}: Got packet {}".format(self.getsrc(packet),
          self.getdst(packet), packet))
      elif "packet" in LOG_PACKETS_DOT:
        sys.stdout.write(".")
        sys.stdout.flush()

    # Fetch the actual ofp__packet_in_message that caused packet to be sent
    # to this controller
    packet_in = event.ofp

    if self.is_client_message(packet):
      self.handle_client_message(event, packet, packet_in)
    elif self.is_paxos_message(packet):
      self.handle_paxos_message(packet, packet_in)
    else:
      # Unknown message type; just leave the packet as is and let any other
      # listeners handle it.
      pass

  def is_paxos_message(self, packet):
    """TODO: Implement."""
    if packet.find("udp"):
      udp = packet.find("udp")
      return paxos.isrecognized(udp.payload)
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

  def drop(self, event, packet):
    """Instructs switch to drop packet."""
    log.info("Dropping packet {}".format(packet))
    msg = openflow.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    self.connection.send(msg)

  def handle_client_message(self, event, packet, packet_in):
    udp = packet.find("udp")
    ip = packet.find("ipv4")

    raw = pickle.loads(udp.payload)
    msg = client.unmarshal(udp.payload)

    if len(msg) < 2:
      log.warning("Could not unmarshal client message: {}".format(raw))
      self.drop(event, packet)
      return
    command, args = msg

    src = self.getsrc(packet)
    dst = self.getdst(packet)

    log.info("{} -> {}: Received client message: {}".format(src, dst, raw))

  def handle_paxos_message(self, packet, packet_in):
    udp = packet.find("udp")
    raw = pickle.loads(udp.payload)
    msg = paxos.unmarshal(udp.payload)
    command, args = msg

    src = self.getsrc(packet)
    dst = self.getdst(packet)

    log.info("{} -> {}: Received paxos message: {}".format(src, dst, raw))

  def is_client_message(self, packet):
    """TODO: Implement."""
    # Is this an UDP message?
    udp = packet.find("udp")
    if udp:
      return client.isrecognized(udp.payload)
    else:
      return False

