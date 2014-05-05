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
import threading
import time

from pox.core import core
from pox.lib.addresses import EthAddr
from pox.lib.packet.ethernet import ETHER_BROADCAST
from pox.lib.revent import EventHalt
from pox.lib.util import dpid_to_str
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from baseline import BaselineController
from paxos.asserts import assert_u32
from paxos.message import PaxosMessage

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


class WANController(object):
  """We want a special controller for the WAN switch, which is the one
  receiving messages from WAN-side clients."""

  def __init__(self,
               connection,
               priority=70,
               quit_on_connection_down=False,
               add_flows=False):

    self.connection = connection
    self.quit_on_connection_down = quit_on_connection_down
    self.add_flows = add_flows

    self.log = core.getLogger("WANCtrl-{}".format(self.connection.ID))
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))
    self.log.info("Connected to {}".format(
      self.connection.description.show()))

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

    # Port connected to the Paxos network
    self.paxos_port = None

  def forward(self, packet_in, port):
     """Instructs switch to forward the packet to the given port."""
     msg = of.ofp_packet_out()
     msg.data = packet_in
     msg.actions.append(of.ofp_action_output(port=port))
     self.connection.send(msg)

  def broadcast(self, packet_in):
    """Forward packet to all nodes."""
    self.forward(packet_in, of.OFPP_ALL)

  def _handle_PacketIn(self, event):
    # We won't do ANYTHING until we've learned which port the Paxos network
    # is on.  This happens when we receive a JOIN.
    packet = event.parsed
    eth = packet.find("ethernet")

    if eth is None:
      self.log.critical("Dropping non-Ethernet packet")
      return EventHalt

    if self.paxos_port is None:
      if eth.type == PaxosMessage.JOIN:
        self.paxos_port = event.port
        self.log.info("Learned that Paxos network is on port {}".
            format(self.paxos_port))

    if self.paxos_port is None:
      self.log.warning("Don't know the Paxos port yet, dropping")
      return EventHalt # Drop packet and stop this particular event

    # Drop packets from the Paxos network
    if event.port == self.paxos_port:
      self.log.warning("Dropping packet from Paxos port")
      # TODO: Add flow for this behaviour, noting that we need to allow
      # certain packets to go OUT to the WAN-side.
      return EventHalt

    # Drop broadcasts
    if packet.dst == ETHER_BROADCAST:
      self.log.info("Dropped broadcast packet")
      return EventHalt

    # Drop everything other than IP packets
    #if not packet.find("ip"):
    #  self.log.warning("Dropping non-IP packet")
    #  return EventHalt

    # Stamp message with Ethernet type PAXOS CLIENT ...
    eth.type = PaxosMessage.CLIENT

    # .. and forward it to the Paxos port
    m = of.ofp_packet_out(data=eth)
    m.actions.append(of.ofp_action_output(port=self.paxos_port))
    self.connection.send(m)

    self.log.debug("Forwarded packet from WAN {}.{} -> {}".format(
      packet.src, event.port, packet.dst))

    # Mark this event as handled
    return EventHalt

  def connectionDown(self, event):
    pass

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
    self.joined = False
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
      self.log.critical("Not an ethernet message {}".format(event))
      return

    if not PaxosMessage.is_paxos_type(eth.type):
      return

    if self.is_client_packet(event.port, eth):
      self.handle_client_packet(event)
      #return self.handle_client_packet(event)

    if PaxosMessage.is_known_paxos_type(eth.type):
      return self.dispatch_paxos(eth.type, event, eth.payload)
    else:
      self.log.warning("Dropping unknown PAXOS message (0x%04x)" % eth.type)
      self.switch.drop(event)
      return EventHalt

  def is_client_packet(self, in_port, eth):
    """Checks if packet comes from the WAN OR has a PAXOS CLIENT type."""
    return PaxosMessage.CLIENT == eth.type

  def handle_client_packet(self, event):
    """Handle client-side WAN packet.
    They must be wrapped in a PAXOS CLIENT type and passed to the leader."""
    # If the message came in on a WAN port, wrap it up and send to leaderA
    self.log.critical("Got client message {}".format(event))
    self.log.info("Passing client message to leader") # TODO
    pass

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

    # We will ONLY dispatch JOIN messages until we've joined the network
    if not self.joined and paxos_type != PaxosMessage.JOIN:
      self.log.warning("Ignoring PAXOS %s message until we've joined" %
          PaxosMessage.get_type(paxos_type))
      return

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
    """Broadcast a PAXOS JOIN message to everyone.
    Will BLOCK until we know about all other connections"""
    def join_block(total_nodes):
      """Blocks until we've joined the Paxos network, aware of all nodes."""
      while True:
        nodes_needed = total_nodes - len(self.state.N)

        # Quit if we did somethin wrong
        if nodes_needed < 0:
          self.log.critical(("Error in setup (can't wait for {} nodes), " +
            "please see source").format(nodes_needed))
          core.quit()
          return

        if nodes_needed == 0:
          self.log.info("Joined Paxos network of {} nodes".format(
            len(self.state.N)))
          break
        src = EthAddr(dpid_to_str(self.connection.dpid))
        self.log.info("Joining Paxos network at {}, need {} more nodes".
            format(src, nodes_needed))
        payload = PaxosMessage.pack_join(self.state.n_id, src.toRaw())
        self.on_join(event=None, payload=payload)

        # Wait for replies from all switches
        if len(self.state.N) < total_nodes:
          time.sleep(0.25)
        else:
          break
      self.joined = True

    # Wait for network joining in a separate thread, so we can continue
    # handling messages here.
    t = threading.Thread(target=join_block,
                         # Minus one for the non-Paxos WAN switch:
                         args=[len(core.openflow.connections)-1])
    t.start()


def add_flows_setting():
  """Returns add_flows setting from environment."""
  if "ADDFLOWS" in os.environ:
    return os.environ["ADDFLOWS"] == "1"
  else:
    return False

def launch():
  """Starts the controller."""
  log = core.getLogger()
  add_flows = add_flows_setting()

  def start_controller(event):
    Controller = PaxosController

    # TODO: Fix this, it's really ugly and hardcoded
    # I think Mininet assigns IDs backwards, so the last switch gets the
    # lowest ID.
    if event.connection.ID == 1:
      Controller = WANController

    log.info("Controller {}, add_flows={}".format(
      Controller.__name__, add_flows))

    Controller(event.connection,
               quit_on_connection_down=True,
               add_flows=add_flows)

  # Launch controller when we detect a connectionUp event
  core.openflow.addListenerByName("ConnectionUp", start_controller)
