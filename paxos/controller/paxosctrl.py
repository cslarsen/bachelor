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

from pox.core import core
#from pox.lib.addresses import EthAddr
from pox.lib.util import dpid_to_str
#import pox.openflow.libopenflow_01 as of

from baseline import BaselineController
from paxos.asserts import assert_u32, assert_u16

class PaxosMessage(object):
  """Interface for creating Paxos-specific messages."""

  # Ethernet type identifiers for Paxos messages as unsigned 16-bit
  # integers.
  JOIN    = 0x7A05
  ACCEPT  = 0x7A06
  LEARN   = 0x7A07
  TRUST   = 0x7A08
  PROMISE = 0x7A09
  PREPARE = 0x7A0A
  CLIENT  = 0x7A0B
  UNKNOWN = 0x0000

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
    if (ethernet_type & 0xFF00) == 0x7A00:
      # Is it a KNOWN Paxos message as well?
      return ethernet_type in PaxosMessage.typemap
    return False

  @staticmethod
  def get_subtype(ethernet_type):
    """Returns the subtype, e.g. JOIN."""
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
  """Contains state for a Paxos instance."""
  def __init__(self, n_id, N):
    """Initializes Paxos state.

    Attributes:
      n_id -- Unique node id
      N -- Total number of Paxos nodes
      crnd -- Current round number
    """
    assert(isinstance(n_id, int))
    assert(isinstance(N, int) and N>0)

    self.n_id = n_id
    self.N = N
    self.crnd = self.n_id

  def pickNext(self):
    """Picks and sets the next current round number (crnd)."""
    self.crnd += self.N
    return self.crnd


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

    self.log = core.getLogger("PaxosSwitch-{}".format(connection.ID))
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))

    # Listen for events from the switch
    connection.addListeners(self, priority=priority)
    connection.addListenerByName("ConnectionDown", self.connectionDown)

  def _handle_PacketIn(self, event):
    """Called when switch upcalls packet in-events."""
    self.handle_paxos(event)
    # The baseline controller gets its own upcalls

  def connectionDown(self, event):
    # The BaselineController will ensure that POX shuts down, so we don't
    # have to do anything more here.
    self.log.info("Connection to switch has gone down")

  def handle_paxos(self, event):
    # is it for US? does it have a paxos 0x7A eth type?
    # if so, handle it
    p = event.parsed

    ptype = p.type

    if PaxosMessage.is_paxos_type(ptype):
      self.log.info("Got ourselves a PAXOS packet here w/type {} -- {}".format(
        PaxosMessage.get_subtype(ptype), hex(ptype)))
      # Instruct others to refrain from processing this packet
      # TODO...
    else:
      self.log.info("Got a packet, but it's not a PAXOS message: {}".format(
        hex(ptype)))


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
