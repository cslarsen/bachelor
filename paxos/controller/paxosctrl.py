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
import sys

from pox.core import core
from pox.lib.addresses import EthAddr
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of

from baseline import BaselineController

class Limits(object):
  """Contains numerical limits."""
  UINT64_MAX = (2 << 63) - 1
  UINT32_MAX = (2 << 31) - 1
  UINT16_MAX = (2 << 15) - 1
  UINT8_MAX  = (2 <<  7) - 1

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
    assert(isinstance(n_id, int) and 0 <= n_id <= Limits.UINT32_MAX)
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
               priority=1,
               quit_on_connection_down=False,
               add_flows=False):

    self.switch = BaselineController(connection,
        priority=priority*2, # Upcalls to PAXOS controller first
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

  def _handle_packetIn(self, event):
    """Called when switch upcalls packet in-events."""
    self.switch._handle_packetIn(event)

  def connectionDown(self, event):
    # The BaselineController will ensure that POX shuts down, so we don't
    # have to do anything more here.
    self.log.info("Connection to switch has gone down")


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

  # Listen to connection up events
  core.openflow.addListenerByName("ConnectionUp", start_controller)

