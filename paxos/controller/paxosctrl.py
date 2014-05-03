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
import socket

from pox.core import core
from pox.lib.addresses import EthAddr
from pox.lib.packet import ethernet
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
  UNKNOWN = 0x7A00

  typemap = {
      ACCEPT:  "ACCEPT",
      CLIENT:  "CLIENT",
      JOIN:    "JOIN",
      LEARN:   "LEARN",
      PREPARE: "PREPARE",
      PROMISE: "PROMISE",
      TRUST:   "TRUST",
      UNKNOWN: "UNKNOWN",
  }

  @staticmethod
  def is_paxos_type(ethernet_type):
    """Checks whether Ethernet type has a PAXOS prefix."""
    assert_u16(ethernet_type)
    # Don't check if we know the subtype
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
  def pack_join(n_id, mac):
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
    self.N = set() # Will be populated by JOINs
    self.crnd = self.n_id

  def pickNext(self):
    """Picks and sets the next current round number (crnd)."""
    assert(len(self.N) > 0)
    self.crnd += self.N
    return self.crnd

  def update_node_set(self, node):
    """Adds a node ID to the set of known Paxos nodes."""
    self.N.update([node])


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

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

    # Note: Connection IDs may not be monotonic, but that shouldn't matter
    # as long as we know about ALL the other nodes.  We start off by sending
    # JOINs.
    self.state = PaxosState(connection.ID)

    self.join_paxos_network()

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
    if eth is not None:
      if PaxosMessage.is_paxos_type(eth.type):
        if PaxosMessage.is_known_paxos_type(eth.type):
          type_name = PaxosMessage.get_type(eth.type)
          self.log.info("Dispatching PAXOS %s (0x%04x)" % (type_name, eth.type))
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
                    PaxosMessage.TRUST:   self.on_trust,
                    PaxosMessage.UNKNOWN: self.on_unknown}

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
    self.state.update_node_set((node_id, EthAddr(mac2str(mac_addr))))

    self.log.critical("Got JOIN w/node_id {} from {}".format(node_id,
      mac2str(mac_addr)))

    self.log.info("We know these nodes now: {}".format(self.state.N))
    # TODO: We could just read the MAC off the source instead?

    # TODO: Should we really drop it? What if we need to rebroadcast some
    # join? Maybe we need to check if the join is meant for US?
    if event is not None:
      self.switch.drop(event)
      return EventHalt

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

  def join_paxos_network(self):
    """Broadcasts PAXOS JOIN message to everyone."""
    # NOTES FROM (TODO)
    # http://lists.noxrepo.org/pipermail/pox-dev-noxrepo.org/2013-July/000893.html
    #
    # You can also get the connections later from the OpenFlow nexus, e.g., using
    # the core.openflow.connections collection which holds a Connection for each
    # connected switch (you can either enumerate it, or you can get connections by
    # their DPID).  There's also the related core.openflow.sendToDPID(dpid,
    # data) method if you know the DPID you want to send to.

    # TODO: Find source MAC for us, can prolly remove it as well?
    src = "a2:e8:da:d3:54:4f"
    e = pkt.ethernet(src=src,
                     dst="ff:ff:ff:ff:ff:ff", # Ethernet broadcast
                     type=PaxosMessage.JOIN)

    node_id = self.state.n_id
    e.payload = PaxosMessage.pack_join(node_id, parse_mac(src))

    #eth = ethernet()
    #eth.set_payload(payload)
    #eth.src = EthAddr("a2:e8:da:d3:54:4f") # hardcoded S1
    #eth.dst = EthAddr("ff:ff:ff:ff:ff:ff")#"5e:29:14:d4:46:47") #ff:ff:ff:ff:ff:ff")
    #eth.type = PaxosMessage.JOIN
    #msg = of.ofp_packet_out(data=eth)
    ##msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL)) # all ports
    #msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL)) # all ports
    #self.connection.send(msg)
    #self.log.debug("Sent out a JOIN: {}".format(eth))

    msg = of.ofp_packet_out(data=e)
    msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL)) # all ports
    self.connection.send(msg)
    self.log.debug("Sent JOIN: {}".format(e))

    # Send to ourself as well by short-circuit
    self.on_join(event=None, payload=e.payload)

    # TODO: FInn ut hvordan resten av join må funke....
    # Feks må være sikre på at alle kjenner alle...
    # Kan feks se, når vi har fått en jion, hvis vi ikke kjenner noden fra
    # før så svarer vi KUN til han der (men broadcaster til alle porter)

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
