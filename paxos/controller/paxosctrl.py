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
    self.vval = None

    # For LEARN, remember number of learns
    # also remember if we have processed it
    self.learned = {}
    self.processed = {}

  def update_learn(self, mac, n):
    """Increase number of learns for n, return this number."""
    if not n in self.learned:
      self.learned[n] = set([mac])
    else:
      self.learned[n].update([mac])
    return len(self.learned[n])

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

    self.log = core.getLogger("WANCtrl-{}".format(self.name))
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))

    # Print which switch and version we're connected to
    desc = self.connection.description
    self.log.info("Connected to {} {}".format(desc.hw_desc, desc.sw_desc))

    self.log.info("Our node name is {} and our MAC is {}".format(
      self.name, self.mac))

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

    # Port connected to the Paxos network
    self.paxos_port = None
    self.wan_macports = {} # MAC->Port for WAN-side

  def forward(self, packet_in, port):
     """Instructs switch to forward the packet to the given port."""
     msg = of.ofp_packet_out()
     msg.data = packet_in
     msg.actions.append(of.ofp_action_output(port=port))
     self.connection.send(msg)

  @property
  def mac(self):
    """Returns our own MAC address."""
    # NOTE: This is a hack, as Mininet assigns the highest port number to
    # the switch interface itself.  This is stuff that may break when we
    # update Mininet!
    ports = self.connection.ports
    return ports[max(ports)].hw_addr

  @property
  def name(self):
    """Returns our name, as given by Mininet."""
    ports = self.connection.ports
    return ports[max(ports)].name

  def broadcast(self, packet_in):
    """Forward packet to all nodes."""
    self.forward(packet_in, of.OFPP_ALL)

  def _handle_PacketIn(self, event):
    # We won't do ANYTHING until we've learned which port the Paxos network
    # is on.  This happens when we receive a JOIN.
    packet = event.parsed
    eth = packet.find("ethernet")
    assert(eth is not None)

    # Sanity check
    if PaxosMessage.is_paxos_type(eth.type):
      if self.paxos_port is not None and event.port != self.paxos_port:
        m = "Paxos message from port {} != known Paxos port {}".format(
              event.port, self.paxos_port)
        self.log.warning(m)

    # Learn which ports Paxos nodes are on
    if self.paxos_port is None:
      if eth.type == PaxosMessage.JOIN:
        self.paxos_port = event.port
        self.log.info("Learned that Paxos network is on port {}".
            format(self.paxos_port))

    # Learn which ports WAN nodes are on
    if self.paxos_port is not None:
      if not PaxosMessage.is_paxos_type(eth.type):
        if not event.port == self.paxos_port:
          if not packet.src in self.wan_macports:
            self.wan_macports[packet.src] = event.port
            self.log.warning("Learned that WAN client {} is on port={}".format(
              packet.src, event.port))

    # TODO: Need to decide how we're going to select what packets to order.
    #       I think UDP and TCP are good.

    if self.from_paxos(event) and (packet.find("udp") or packet.find("tcp")):
      return self.send_to_paxos(event)

    # Packets from Paxos are sent to the WAN side only
    if self.from_paxos(event):
      return self.send_to_wan(event)

    # In case clients want to talk (TODO: does not work yet)
    if self.from_wan(event) and self.to_wan(event):
      return self.send_to_wan(event)

    # For other packets, just forward to Paxos port
    self.log.info("Forwarding unknown packet to Paxos network {}.{} -> {} at {}".
        format(packet.src, event.port, packet.dst, self.paxos_port))
    self.forward(event.ofp, port=self.paxos_port)
    return EventHalt

    # NOTE: One thing is missing, if clients want to reach each other

    self.log.warning("Should not reach here!!")
    return EventHalt

  def from_paxos(self, event):
    """See if packet comes from Paxos network."""
    return event.port == self.paxos_port

  def from_wan(self, event):
    """See if packet comes from the WAN."""
    return not self.from_paxos(event)

  def to_wan(self, event):
    """See if packet is destined to WAN."""
    # TODO: In case of broadcasts, send both to WAN and Paxos?
    return event.parsed.dst in self.wan_macports.keys()

  def is_broadcast(self, event):
    return event.parsed.dst == ETHER_BROADCAST

  def connectionDown(self, event):
    pass

  def send_to_paxos(self, event):
    """Wrap in PAXOS CLIENT and send to Paxos network."""
    if self.paxos_port is None:
      self.log.warning("Don't know which port Paxos is on, drop.")
      return EventHalt

    # Stamp message with type PAXOS CLIENT
    eth = event.parsed.find("ethernet")
    eth.type = PaxosMessage.CLIENT
    eth.payload = PaxosMessage.pack_client(eth.raw)

    # Forward wrapped message to Paxos network
    m = of.ofp_packet_out(data=eth)
    m.actions.append(of.ofp_action_output(port=self.paxos_port))
    self.connection.send(m)

    self.log.debug("Wrapped WAN packet {}.{}->{} and sent to Paxos.".format(
      eth.src, event.port, eth.dst))
    return EventHalt

  def send_to_wan(self, event):
    """Sends packet to the WAN network."""
    packet = event.parsed

    # Forward to known destination port
    if packet.dst in self.wan_macports:
      self.log.info("Forwarding packet dst={} to known WAN port {}".
          format(packet.dst, self.wan_macports[packet.dst]))
      self.forward(event.ofp, port=self.wan_macports[packet.dst])
      return

    # Forward to all WAN ports
    for port in self.wan_macports.values():
      self.log.info("Forwarding packet dst={} to WAN port {}".format(
        packet.dst, port))
      self.forward(event.ofp, port=port)


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

    # Set up attributes BEFORE listening to the network, otherwise we could
    # get in concurrency trouble.
    self.joined = False
    #
    # Note: Connection IDs may not be monotonic, but should be unique. We
    # can therefore use it as a node ID.
    self.quit_on_connection_down = quit_on_connection_down
    self.connection = connection
    self.paxos_ports = {}
    self.log = core.getLogger("PaxosCtrl-{}-[{}]".format(self.name, self.mac))

    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))

    # Print which switch and version we're connected to
    desc = self.connection.description
    self.log.info("Connected to {} {}".format(desc.hw_desc, desc.sw_desc))
    self.log.info("Our node name is {} and our MAC is {}".format(
      self.name, self.mac))

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

    self.state = PaxosState(int(self.name[-1])) # NOTE: See self.name note

    self.switch = BaselineController(connection,
        priority=50, # lower pri so we process first
        quit_on_connection_down=quit_on_connection_down,
        add_flows=add_flows,
        name_prefix="Switch-" + self.name,
        name_suffix=False)

    # Start by broadcasting PAXOS JOIN to learn about all the other Paxos
    # nodes
    self.join_network()

  def _handle_PacketIn(self, event):
    """Called when switch upcalls packet in-events."""
    return self.handle_paxos(event)
    # The baseline controller gets its own upcalls

  def connectionDown(self, event):
    # The BaselineController will ensure that POX shuts down, so we don't
    # have to do anything more here.
    self.log.info("Connection to switch has gone down")

  def handle_paxos(self, event):
    # Ignore anything but Paxos-messages
    eth = event.parsed.find("ethernet")
    assert(eth is not None)

    if PaxosMessage.is_known_paxos_type(eth.type):
      # React on messages form WAN, JOINs, to us or broadcasts
      dispatch = self.is_wan_port(event.port)
      dispatch |= eth.type == PaxosMessage.JOIN
      dispatch |= eth.dst == self.mac
      dispatch |= eth.dst == ETHER_BROADCAST

      if dispatch:
        return self.dispatch_paxos(eth.type, event, eth.payload)

    # Silently ignore other messages; let the switch handle those
    pass

  def is_wan_port(self, port):
    return port not in self.paxos_ports.values()

  def is_client_packet(self, in_port, eth):
    """Checks if packet comes from the WAN OR has a PAXOS CLIENT type."""
    return PaxosMessage.CLIENT == eth.type

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

  def on_accept(self, event, message):
    n, v = PaxosMessage.unpack_accept(message)

    # Did we send to ourself?
    if event is not None:
      src = event.parsed.src
      dst = event.parsed.dst
    else:
      src = self.mac
      dst = self.mac

    self.log.info("On ACCEPT n={} crnd={} from {}->{}".format(
      n, self.state.crnd, src, dst))

    # NOTE: For debugging
    if n > 10:
      self.log.critical("Shutting down on flood")
      core.quit()
      return EventHalt

    if n >= self.state.crnd:
      self.state.crnd = n
      self.state.vval = v
      for mac in self.state.N:
        self.log.info("Sending LEARN n={} to {}".format(n, mac))
        self.send_learn(mac, n, v, self.lookup_port(mac))

    return EventHalt

  def lookup_port(self, mac):
    """Returns port MAC address is on or BROADCAST if not found."""
    if mac in self.switch.macports:
      return self.switch.macports[mac]
    else:
      if mac != self.mac:
        self.log.warning("Don't know which port {} is on, know these {}".
            format(mac, self.switch.macports))
      return of.OFPP_ALL

  @property
  def mac(self):
    """Returns our own MAC address."""
    # NOTE: This is a hack, as Mininet assigns the highest port number to
    # the switch interface itself.  This is stuff that may break when we
    # update Mininet!
    ports = self.connection.ports
    return ports[max(ports)].hw_addr

  @property
  def name(self):
    """Returns our name, as given by Mininet."""
    ports = self.connection.ports
    return ports[max(ports)].name

  def on_client(self, event, message):
    # TODO: if leader, send out accept
    # TODO: if not, forward to leader

    # Did we send to ourself?
    if event is not None:
      src = event.parsed.src
      dst = event.parsed.dst
    else:
      src = self.mac
      dst = self.mac


    payload = PaxosMessage.unpack_client(message)

    n = self.state.pickNext() #self.state.crnd  # TODO: This is incorrect

    self.log.info("On CLIENT from n={} {} to {}".format(n, src, dst))

    for mac in self.state.N:
      self.log.info("Sending ACCEPT n={} from {} to {}".format(n,
        self.mac, mac))

      v = payload # TODO: send buffer id instead
      self.send_accept(mac, n, v, self.lookup_port(mac))

    return EventHalt

  def send_accept(self, dst, n, v, port):
    payload = PaxosMessage.pack_accept(n, v)

    # Short-circuit messages to ourself
    if dst == self.mac:
      self.on_accept(event=None, message=payload)
    else:
      return self.send_ethernet(src=self.mac,
                                dst=dst,
                                type=PaxosMessage.ACCEPT,
                                payload=payload,
                                output_port=port)

  def send_learn(self, dst, n, v, port):
    payload = PaxosMessage.pack_learn(n, v)

    # Short-circuit messages to ourself
    if dst == self.mac:
      self.on_learn(event=None, message=payload)
    else:
      return self.send_ethernet(src=self.mac,
                                dst=dst,
                                type=PaxosMessage.LEARN,
                                payload=payload,
                                output_port=port)

  def on_join(self, event, message):
    node_id, mac_addr = PaxosMessage.unpack_join(message)
    mac = EthAddr(mac_addr)

    self.log.info("JOIN from {}, |N|={}".format(
      mac, len(self.state.nodes)))

    # Only react on new nodes
    if mac not in self.state.nodes:
      if event is not None:
        self.paxos_ports[mac] = event.port
      self.state.add_node(mac)
      src = self.mac

      # Also add node to the switch, so it knows where to direct packets
      # This is very important, or else all Paxos-messages will end up as
      # broadcasts.
      if event is not None:
        self.switch.learn_port(mac, event.port)

      # Self-generated join? (join on self)
      if event is None:
        self.log.info("Broadcasting JOIN from {}".format(src))
        dst = ETHER_BROADCAST
        port = of.OFPP_ALL
      else:
        self.log.info("Sending JOIN back from {} to {}".format(
          self.mac, mac))
        dst = mac_addr
        port = event.port

      self.send_ethernet(src=src,
                         dst=dst,
                         type=PaxosMessage.JOIN,
                         payload=PaxosMessage.pack_join(
                           self.state.n_id, EthAddr(src).toRaw()),
                         output_port=port)

  def on_learn(self, event, message):
    n, v = PaxosMessage.unpack_learn(message)

    # Did we send to ourself?
    if event is not None:
      src = event.parsed.src
      dst = event.parsed.dst
    else:
      src = self.mac
      dst = self.mac

    self.log.info("On LEARN from {} to {}".format(src, dst))

    if n in self.state.processed:
      self.log.warning("Already processed n=%d" % n)
      return EventHalt

    learns = self.state.update_learn(src, n)
    needed = 1 + (len(self.state.N)//2)

    # Got majority?
    if learns >= needed:
      if not n in self.state.processed:
        self.log.info("On LEARN, will act on n=%d learns=%d / %d" % (n,
          learns, needed))
        self.state.processed[n] = True

        # TODO: Pass on to host, but if not to one of our hosts, then
        #       just drop it (or pass on to others; note that we should
        #       add a rule that we dont broadcast back to ingress port
        #       (or, don't add rules for it)
        return self.process_message(v)
    else:
      self.log.info("On LEARN n=%d, have %d votes, need %d" % (
        n, learns, needed))

    return EventHalt

  def process_message(self, v):
    """Act on a Paxos value that reached consensus."""

    # This is a raw Ethernet packet
    eth = pkt.ethernet(raw=v)

    # TODO: Pass the packet on to each of our hosts, changing the
    # destination address for each one of them.  This is the core of the
    # mirroring in this system.

    # FIXME: For now, just broadcast it
    self.log.critical("PROCESS, got packet %s->%s type=0x%04x" % (
      eth.src, eth.dst, eth.type))

    # Known destination port? Forward it then.
    # TODO / NOTE: We need to discern between HOSTS and WAN here...
    #              We don't have a total map of the network...
    if eth.dst in self.switch.macports:
      # Don't forward OUT to another switch
      if eth.dst not in self.paxos_ports:
        self.log.debug("Forwarding process msg to port {}".format(
          self.switch.macports[eth.dst]))

        port = self.switch.macports[eth.dst]
        m = of.ofp_packet_out(data=eth)
        m.actions.append(of.ofp_action_output(port=port))
        self.connection.send(m)
        return EventHalt
      else:
        self.log.warning("Will not forward to other Paxos nets")
        return EventHalt
    else:
      self.log.warning("Unknown destination")
      return EventHalt

    # Send to all ports that are not Paxos-ports?
    for port in self.connection.ports:
      if port in self.paxos_ports.values():
        continue
      if port > 10000:
        continue

      m = of.ofp_packet_out(data=eth)
      m.actions.append(of.ofp_action_output(port=port))
      self.connection.send(m)

    return EventHalt

  def on_prepare(self, event, message):
    self.log.critical("Unimplemented on_prepare, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_promise(self, event, message):
    self.log.critical("Unimplemented on_promise, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_trust(self, event, message):
    self.log.critical("Unimplemented on_trust, dropping")
    self.switch.drop(event)
    return EventHalt

  def on_unknown(self, event, message):
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
        src = self.mac
        self.log.info("Joining Paxos network at {}, need {} more nodes".
            format(src, nodes_needed))
        payload = PaxosMessage.pack_join(self.state.n_id, src.toRaw())
        self.on_join(event=None, message=payload)

        # Wait for replies from all switches
        if len(self.state.N) < total_nodes:
          time.sleep(0.25)
        else:
          break
      self.joined = True

    # Wait for network joining in a separate thread, so we can continue
    # handling messages here.
    #
    # NOTE: We only REQUIRE at least three components (one can fail, two can
    # continue).  There is no way for POX to get the number of switches
    # (that I have found).  Anyway, the topology has been set up with three
    # components.
    t = threading.Thread(target=join_block, args=[3])
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
    # NOTE: Here we have hardcoded the WAN switch from the topology.
    #       So this only works with the correct topology (PaxosTopology).
    if "WAN1" in [p.name for p in event.connection.ports.values()]:
      Controller = WANController
    else:
      Controller = PaxosController

    name = Controller.__name__
    log.info("Controller {}, add_flows={}".format(name, add_flows))

    Controller(event.connection,
               quit_on_connection_down=True,
               add_flows=add_flows)

  # Launch controller when we detect a connectionUp event
  core.openflow.addListenerByName("ConnectionUp", start_controller)
