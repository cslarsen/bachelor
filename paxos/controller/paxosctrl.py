# -*- encoding: utf-8 -*-

"""
Contains a Paxos OpenFlow controller.

Here we implement everything possible as flows, and leave the rest in the
controller.  This is different from placing Paxos on the switch itself.

This serves two purposes:

  1. We want to show that it's possible to perform mirroring using Paxos as
     a controller, and
  2. We want to use it as a baseline to see if Goxos (a Paxos implementation
     entirely in software) or Paxos-on-switch is faster.

Our hypothesis is that this controller will be faster than Goxos but slower
than Paxos-on-the-switch.
"""


from struct import pack, unpack
import os
import random
import socket
import time

from pox.core import core
from pox.lib.addresses import EthAddr
from pox.lib.packet import ethernet
from pox.lib.packet.ethernet import ETHER_BROADCAST
from pox.lib.revent import EventHalt
from pox.lib.util import dpid_to_str
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from baseline import BaselineController
from paxos.asserts import assert_u32, assert_u16
from paxos.ethernet import str2mac, mac2str, parse_mac

class PaxosMessage(object):
  """Interface for creating Paxos-specific messages."""

  # Ethernet type identifiers for Paxos messages as unsigned 16-bit
  # integers.  They can be anything larger than 0x0600 (per the standard).
  JOIN    = 0x7A05
  ACCEPT  = 0x7A06
  LEARN   = 0x7A07
  TRUST   = 0x7A08
  PROMISE = 0x7A09
  PREPARE = 0x7A0A
  CLIENT  = 0x7A0B

  typemap = {
      ACCEPT:  "ACCEPT",
      CLIENT:  "CLIENT",
      JOIN:    "JOIN",
      LEARN:   "LEARN",
      PREPARE: "PREPARE",
      PROMISE: "PROMISE",
      TRUST:   "TRUST",
  }

  @staticmethod
  def is_paxos_type(ethernet_type):
    """Checks whether Ethernet type has a PAXOS prefix."""
    return (ethernet_type & 0xFF00) == 0x7A00

  @staticmethod
  def is_known_paxos_type(ethernet_type):
    return ethernet_type in PaxosMessage.typemap

  @staticmethod
  def get_type(ethernet_type):
    """Returns the type of Paxos message as string, e.g. 'JOIN'."""
    assert(PaxosMessage.is_paxos_type(ethernet_type))
    return PaxosMessage.typemap[ethernet_type]

  @staticmethod
  def pack_join(n_id, mac): # TODO: Don't need any payload here...
    """Creates a PAXOS JOIN message.

    Arguments:
      n_id -- The instance's unique node id (unsigned 32-bit network order)
      mac -- The instance's MAC address in raw wire-format (a string).

    Note that we don't care about conforming to any particular ABI here
    (e.g. ARMs require word-alignment).  This is only a bachelor's thesis,
    after all.

    Returns:
      A 10-byte message containing NODE_ID (unsigned 32-bit big-endian,
      network order, integer) and the raw MAC address (unsigned 48-bit
      integer).
    """
    assert_u32(n_id)
    assert(isinstance(mac, str) and len(mac) == 6)
    return pack("!I", n_id) + mac

  @staticmethod
  def unpack_join(payload):
    """Unpacks a PAXOS JOIN message.

    Returns:
      Tuple of (mac, node_id) where the MAC-address is in raw format and
      node_id is an unsigned 32-bit integer in host endianness.
    """
    assert(isinstance(payload, str) and len(payload) == 6+4)
    n_id = unpack("!I", payload[0:4])[0]
    mac = payload[4:]
    return n_id, mac

class PaxosState(object):
  """Contains state for a Paxos instance that inhibits all roles."""
  def __init__(self, n_id):
    """Initializes Paxos state.

    Attributes:
      n_id -- Unique node id
      N -- Node ids of ALL Paxos nodes (including ourself)
      crnd -- Current round number
    """
    assert(isinstance(n_id, int))

    self.n_id = n_id
    self.N = set()
    self.crnd = self.n_id

  def pickNext(self):
    """Picks and sets the next current round number (crnd)."""
    assert(len(self.N) > 0)
    self.crnd += len(self.N)
    return self.crnd

  def add_node(self, node):
    """Adds a node to the set of known Paxos nodes."""
    self.N.update([node])

  @property
  def nodes(self):
    """Returns sorted set of known Paxos nodes."""
    return sorted(self.N)


class PaxosController(object):
  """A Paxos controller using the baseline L2 learning switch (without
  flows) to perform forwarding.  We can't install forwarding flows because
  we want to intercept certain messages (we can probably switch on flows for
  the switch later on when everything works).
  """

  def __init__(self,
               connection,
               priority=100,
               quit_on_connection_down=False,
               add_flows=False):

    self.switch = BaselineController(connection,
        priority=50, # lower pri so we process first
        quit_on_connection_down=quit_on_connection_down,
        add_flows=add_flows)

    self.connection = connection
    self.quit_on_connection_down = quit_on_connection_down

    self.log = core.getLogger("PaxosCtrl-{}".format(self.connection.ID))
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))
    self.log.info("Connected to {}".format(
      self.connection.description.show()))

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

    # Note: Connection IDs may not be monotonic, but should be unique. We
    # can therefore use it as a node ID.
    self.state = PaxosState(connection.ID)

    # Start by broadcasting JOIN
    self.join_network()

  def _handle_PacketIn(self, event):
    """Called when switch upcalls packet in-events."""
    self.handle_paxos(event)
    # The baseline controller gets its own upcalls

  def connectionDown(self, event):
    # The BaselineController will ensure that POX shuts down, so we don't
    # have to do anything more here.
    self.log.info("Connection to switch has gone down")

  def handle_paxos(self, event):
    # Ignore anything but Paxos-messages
    eth = event.parsed.find("ethernet")

    if eth is None:
      return

    if not PaxosMessage.is_paxos_type(eth.type):
      return

    if PaxosMessage.is_known_paxos_type(eth.type):
      type_name = PaxosMessage.get_type(eth.type)
      return self.dispatch_paxos(eth.type, event, eth.payload)
    else:
      self.log.warning("Dropping unknown PAXOS message (0x%04x)" % eth.type)
      self.switch.drop(event)
      return EventHalt

  def dispatch_paxos(self, paxos_type, event, payload):
    """Dispatch to message handlers based on Paxos message type."""
    assert(PaxosMessage.is_paxos_type(paxos_type))

    dispatch_map = {PaxosMessage.ACCEPT:  self.on_accept,
                    PaxosMessage.CLIENT:  self.on_client,
                    PaxosMessage.JOIN:    self.on_join,
                    PaxosMessage.LEARN:   self.on_learn,
                    PaxosMessage.PREPARE: self.on_prepare,
                    PaxosMessage.PROMISE: self.on_promise,
                    PaxosMessage.TRUST:   self.on_trust}

    handler = dispatch_map[paxos_type]
    return handler(event, payload)

  def on_accept(self, event, payload):
    self.log.critical("Unimplemented on_accept, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_client(self, event, payload):
    self.log.critical("Unimplemented on_client, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_join(self, event, payload):
    node_id, mac_addr = PaxosMessage.unpack_join(payload)
    mac = EthAddr(mac_addr)

    self.log.info("JOIN from {}, |N|={}".format(
      mac, len(self.state.nodes)))

    # Only react on new nodes
    if mac not in self.state.nodes:
      self.state.add_node(mac)
      src = dpid_to_str(self.connection.dpid)

      # Self-generated join? (join on self)
      if event is None:
        self.log.info("Broadcasting JOIN from {}".format(src))
        dst = ETHER_BROADCAST
        port = of.OFPP_ALL
      else:
        self.log.info("Sending JOIN back to {}".format(mac))
        dst = mac_addr
        port = event.port

      self.send_ethernet(src=src, dst=dst,
                         type=PaxosMessage.JOIN,
                         payload=PaxosMessage.pack_join(
                           self.state.n_id, EthAddr(src).toRaw()),
                         output_port=port)

  def on_learn(self, event, payload):
    self.log.critical("Unimplemented on_learn, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_prepare(self, event, payload):
    self.log.critical("Unimplemented on_prepare, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_promise(self, event, payload):
    self.log.critical("Unimplemented on_promise, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_trust(self, event, payload):
    self.log.critical("Unimplemented on_trust, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_unknown(self, event, payload):
    self.log.critical("Unimplemented on_unknown, dropping")
    self.switch.drop(event)
    return EventHalt

  def send_ethernet(self, src, dst, type, payload, output_port):
    """Sends a raw Ethernet frame on the network."""
    packet = pkt.ethernet(src=src, dst=dst, type=type)
    packet.payload = payload

    m = of.ofp_packet_out(data=packet)
    m.actions.append(of.ofp_action_output(port=output_port))
    return self.connection.send(m)

  def join_network(self):
    """Broadcast a PAXOS JOIN message to everyone."""
    while True:
      src = EthAddr(dpid_to_str(self.connection.dpid))
      self.log.info("Joining Paxos network, {}".format(src))
      payload = PaxosMessage.pack_join(self.state.n_id, src.toRaw())
      self.on_join(event=None, payload=payload)

      # Wait for replies
      if len(self.state.N) > 0:
        break
      else:
        time.sleep(random.randint(1,2))


def launch():
  """Starts the controller."""
  log = core.getLogger()
  Controller = PaxosController

  add_flows = True
  if "ADDFLOWS" in os.environ:
    if os.environ["ADDFLOWS"] == "1":
      add_flows = True
    elif os.environ["ADDFLOWS"] == "0":
      add_flows = False
    else:
      log.warning("Unknown ADDFLOWS value: %s" % os.environ["ADDFLOWS"])

  def start_controller(event):
    Controller(event.connection,
               quit_on_connection_down=True,
               add_flows=add_flows)

  log.info("POX controller {}".format(Controller.__name__))
  log.info("Add flows set to {}".format(add_flows))
  log.info("Switch upcalls sends first {} bytes of each packet".
      format(core.openflow.miss_send_len))
  log.info("Now try:\nh1 python ~/bach/paxos/commandline/send-eth " +
           "ee:95:30:c3:51:37 6a:39:9c:45:cb:45 0x7a05 h1-eth0 'hello'\n")

  # Listen to connection up events
  core.openflow.addListenerByName("ConnectionUp", start_controller)
