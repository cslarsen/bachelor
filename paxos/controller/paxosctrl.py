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

TODO (prioritized):
  1. Change ether dst and IP dst when sending to hosts
     - Also send to each host; need to know them
  2. Send packet IDs in v instead of full packet
     - This needs a special way to transmit messages to other controllers and
       tell them to store the packet.

TODO (unsorted):
  - If the WAN-controller does not know the Paxos network, create an
    announce parameter in JOIN so that they can ask who are present.
  - In is_broadcast_dst, wrap in pk.ethernet() and use .isbroadcast on that.
  - Controllers need to know who is leader, so they can install flows to
    forward client messages, for instance.
  - There is no matching on ethernet_type in OVS/OF, extend?
  - Learn IP-addresses in addition to MACs, so ip->mac, mac->port
"""


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
from paxos.message import PaxosMessage


class Slot(object):
  """A Paxos slot."""
  def __init__(self, vrnd, vval, node_count):
    # Acceptor
    self.vrnd = vrnd
    self.vval = vval

    # Learner
    self.learns = set()
    self.hrnd = 0 # highest round we received learn on
    self.value = None

    self.node_count = node_count

  def __str__(self):
    return "<Slot: vrnd={} vval={} hrnd={} learns={} |value|={} nodes={}>".format(
      self.vrnd, self.vval, self.hrnd, self.learns, len(self.value),
      self.node_count)

  def reset_learns(self):
    self.learns = set()

  @property
  def votes(self):
    """Returns number of unique learns we have gotten."""
    return len(self.learns)

  def update_learns(self, obj):
    """Add a (unique) object to set of learns."""
    self.learns.update([obj])

  @property
  def required_learns(self):
    """Returns the minimum number of learns (or votes) required for a
    majority (or quorum)."""
    return 1 + self.node_count // 2

  @property
  def learned(self):
    """Check whether we have a majority of learns."""
    return self.votes >= self.required_learns


class Slots(object):
  """Contains many Slots."""
  def __init__(self, node_count=None):
    self.slots = {} # NOTE: Should be a heap or pri-queue
    self._node_count = node_count
    self._cseq = 0
    self.processed = set() # TODO: do we need this?

  def queue(self):
    """
    Starting from the current sequence number, return tuples of (seqno,
    slot) for processing.  Stop whenever there is a gap in sequence numbers.
    """
    # Increase cseq by one and stop whenever there is a gap
    while self._cseq in self.slots:
      slot = self.slots[self._cseq]

      # All slots must be learned
      if not slot.learned:
        return

      yield self._cseq, self.slots[self._cseq]

      # Advance to next
      self._cseq += 1

  def update_node_count(self, node_count):
    """Set number of nodes for this round. Affects all slots."""
    self._node_count = node_count
    for slot in self.slots:
      slot.node_count = self._node_count

  def get_slot(self, seqno):
    """Get given slot, or return a new one."""
    if not seqno in self.slots:
      self.slots[seqno] = Slot(None, None, self._node_count)
    return self.slots[seqno]

  def set_processed(self, n, seqno):
    self.processed.update([(n, seqno)])

  def is_processed(self, n, seqno):
    return (n, seqno) in self.processed

  def garbage_collect(self, n):
    """Remove processed slots."""
    # TODO: Could also remove slots with hrnd < n
    for (seqno, slot) in self.slots:
      if self.is_processed(n, seqno):
        del self.slots[seqno]


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

    self.n_id = n_id      # Our unique ID
    self.N = set()        # Ethernet addresses of ALL Paxos nodes
    self.crnd = self.n_id # Current round number

    # Contains PaxosSlots
    self.slots = Slots(len(self.N))

  def next_round(self):
    """Initializes a new round."""
    self.pickNext()
    self.slots.update_node_count(len(self.N))

  def pickNext(self):
    """Picks and sets the next current round number (crnd)."""
    assert(len(self.N) > 0)
    self.crnd += len(self.N)
    return self.crnd

  def add_node(self, node):
    """Adds a node to the set of known Paxos nodes."""
    self.N.update([node])
    self.slots.update_node_count(len(self.N))

  def ordered_nodes(self, last_node):
    """Returns a set of Paxos nodes, last_node last."""
    v = sorted(list(self.N))
    v.remove(last_node)
    v.append(last_node)
    return v

  @property
  def node_count(self):
    return len(self.N)

  def __str__(self):
    """Returns string-representation of state."""
    return "<PaxosState: n_id={} crnd={} |N|={}>".format(
            self.n_id, self.crnd, len(self.N))


class Leader(object):
  """Contains values needed for leader."""
  def __init__(self):
    self.seqno = None

  def next_seqno(self):
    if self.seqno is None:
      self.seqno = 0
    else:
      self.seqno += 1
    return self.seqno


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
    self.log.debug("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))

    # Print which switch and version we're connected to
    desc = self.connection.description
    self.log.debug("Connected to {} {}".format(desc.hw_desc, desc.sw_desc))

    self.log.debug("Our node name is {} and our MAC is {}".format(
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
    """Returns our own MAC address as a string."""
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
    # is on (see below).  This happens when we receive a JOIN.
    packet = event.parsed
    eth = packet.find(pkt.ethernet)
    assert(eth is not None)

    # Sanity check
    if PaxosMessage.is_paxos_type(eth.type):
      if self.paxos_port is not None and event.port != self.paxos_port:
        m = "Paxos message from port {} != known Paxos port {}".format(
              event.port, self.paxos_port)
        self.log.warning(m)

    # Learn which ports Paxos nodes are on
    if self.paxos_port is None and eth.type == PaxosMessage.JOIN:
      self.paxos_port = event.port
      self.log.debug("Learned that Paxos network is on port {}".
          format(self.paxos_port))

    # Learn which ports WAN nodes are on
    if self.paxos_port is not None:                # We know the Paxos port,
      if not PaxosMessage.is_paxos_type(eth.type): # it's not a Paxos msg,
        if not event.port == self.paxos_port:      # not from the Paxos net
          if not packet.src in self.wan_macports:  # and it's new.
            self.wan_macports[packet.src] = event.port
            self.log.debug("Learned that WAN client {} is on port={}".
              format(packet.src, event.port))

    # IF we don't know the Paxos port number, it means that they haven't
    # joined.  Let's ask them for an announcement in that case
    if self.paxos_port is None:
      self.log.warning("The Paxos network is unknown to us, dropping packet.")
      # TODO: Implement announce message
      return EventHalt

    # NOTE: There are all kinds of packets flowing on the network, including
    #       ARPs, ICMPs, TCP SYN and SYN+ACKs, etc.  To be able to look up
    #       IP-addresses, one needs certain packages to flow freely.  We
    #       cannot perform Paxos ordering on all of them.
    #
    #       So we have decided to ONLY act on TCP and UDP packets.  This
    #       seem to be a good choice.

    # Packets bound TO Paxos that are UDP or TCP, wrap and forward
    if self.to_paxos_addr(event):
      if packet.find(pkt.udp) or packet.find(pkt.tcp):
        return self.wrap_and_send_to_paxos(event)

    # Packets from Paxos are sent to the WAN side only
    if self.to_wan_addr(event):
      return self.forward_to_wan(event)

    # In case clients want to talk
    if self.from_wan_port(event) and self.to_wan_addr(event):
      return self.forward_to_wan(event)

    # Broadcasts should go to all
    if event.parsed.dst == ETHER_BROADCAST:
      # For other packets, just forward to Paxos port
      self.log.debug("Broadcast {}.{} -> {}".format(
          packet.src, event.port, packet.dst))
      self.forward(event.ofp, port=of.OFPP_ALL)
      return EventHalt
    else:
      # For other packets, just forward to Paxos port
      self.log.debug("WAN -> PAX (type {}) {}.{} -> {}.{}".format(
        "0x%04x" % packet.type, packet.src, event.port, packet.dst,
        self.paxos_port))
      self.forward(event.ofp, port=self.paxos_port)
      return EventHalt

  def from_paxos_port(self, event):
    """See if packet comes from Paxos network."""
    return event.port == self.paxos_port

  def to_paxos_addr(self, event):
    """See if packet is destined to Paxos network."""
    return not self.to_wan_addr(event)

  def from_wan_port(self, event):
    """See if packet comes from the WAN."""
    return not self.from_paxos_port(event)

  def to_wan_addr(self, event):
    """See if packet is destined to WAN."""
    return event.parsed.dst in self.wan_macports.keys()

  def from_wan_addr(self, event):
    return event.parsed.src in self.wan_macports.keys()

  def is_broadcast_dst(self, event):
    # TODO: Can find("ethernet") and do isbroadcast on it
    return event.parsed.dst == ETHER_BROADCAST

  def connectionDown(self, event):
    pass

  def wrap_and_send_to_paxos(self, event):
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

    self.log.info("Sending WAN CLIENT packet {}.{}->{} len={} and sent to Paxos.".format(
            eth.src, event.port, eth.dst, len(eth.raw)))

    self.connection.send(m)
    return EventHalt

  def port_name(self, port):
    if self.paxos_port is not None:
      if port == self.paxos_port:
        return "PAX"
      else:
        return "WAN"
    else:
      return "?"

  def forward_to_wan(self, event):
    """Sends packet to the WAN network."""
    packet = event.parsed

    # Forward to known destination port
    if packet.dst in self.wan_macports:
      self.log.debug("{} -> WAN (type {}) {}.{} -> {}.{}".
          format(self.port_name(event.port), "0x%04x" % packet.type, packet.src,
                 event.port, packet.dst, self.wan_macports[packet.dst]))
      self.forward(event.ofp, port=self.wan_macports[packet.dst])
      return

    # Forward to all WAN ports
    for port in self.wan_macports.values():
      self.log.debug("{} -> WAN (type {}) {}.{} -> {}.{}".format(
        self.port_name(event.port), "0x%04x" % packet.type,
        packet.src, event.port, packet.dst, port))
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
    self.log = core.getLogger("PaxosCtrl-{} {}".format(self.name, self.mac))

    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))

    if add_flows:
      self.log.warning("Flows turned ON!")

    # Print which switch and version we're connected to
    desc = self.connection.description
    self.log.debug("Connected to {} {}".format(desc.hw_desc, desc.sw_desc))
    self.log.debug("Our node name is {} and our MAC is {}".format(
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
        name_suffix=False,
        learn_ip_addresses=True,
        clear_flows_on_startup=True)

    # Start by broadcasting PAXOS JOIN to learn about all the other Paxos
    # nodes
    self.join_network()

    # If we are leader, set the next round number so that it's bigger than
    # the other ones.  Since join_network runs asynchronously (in its own
    # thread), we have to wait until we have joined.
    #
    # The target here with pickNext is a hardcoded way to send ourself a
    # TRUST message (see the thesis).  This could be sent from Mininet, but
    # we should onl do it when we know all the other Paxos nodes.
    #
    if self.isleader():
      self.async_wait_joined(timeout=10, quit_on_timeout=True,
                             target=self.next_round)

  def next_round(self):
    """Initiates a new round."""
    if self.isleader():
      if not hasattr(self, "leader"):
        self.leader = Leader()
      self.state.pickNext()

  def async_wait_joined(self,
                       timeout=10,
                       quit_on_timeout=False,
                       target=lambda: 0):
    """Block until we have joined the Paxos network."""

    def wait_join(timeout, quit, target):
      while not self.joined:
        if timeout < 10:
          self.log.warning("Leader waiting {} more secs to join Paxos network".
              format(timeout))

        # Send a new PAXOS JOIN broadcast every three seconds
        if (timeout % 3) == 0:
          self.log.warning("Leader asking again to join Paxos network.")
          self.send_join(dst=ETHER_BROADCAST, port=of.OFPP_ALL)

        timeout -= 1
        if timeout <= 0:
          self.log.warning("Timed out waiting for network join")
          if not quit_on_timeout:
            return
          else:
            self.log.critical("Stopping controller, please restart.")
            core.quit()
            return

        # Wait 1 second in small increments, or else it will take at least
        # one second before the leader joins.
        for _ in xrange(10):
          if self.joined: break
          time.sleep(0.1)

      # Run target if we did not time out
      if self.joined:
        self.log.info("\n" +
            "--------------------------------------\n" +
            "Leader joined Paxos network of %d nodes\n" %
              self.state.node_count  +
            "--------------------------------------")
        target()

    threading.Thread(target=wait_join,
                     args=(timeout, quit_on_timeout, target)).start()

  def _handle_PacketIn(self, event):
    """Called when switch upcalls packet in-events."""
    # The baseline controller (L2 switch) gets its own upcalls
    return self.handle_paxos(event)

  def connectionDown(self, event):
    # The BaselineController will ensure that POX shuts down, so we don't
    # have to do anything more here.
    self.log.warning("Connection to switch has gone down")

  def handle_paxos(self, event):
    # Ignore anything but Paxos-messages
    eth = event.parsed.find(pkt.ethernet)
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
    n, seqno, v = PaxosMessage.unpack_accept(message)
    src, dst = self.get_ether_addrs(event)

    # TODO: Verify that it is from the leader
    if dst != self.mac:
      self.log.warning("Got ACCEPT from {} not addressed to us, drop".
          format(src))
      return EventHalt

    self.log.info("On ACCEPT n={} seq={} from {}".format(
      n, seqno, src))

    slot = self.state.slots.get_slot(seqno)

    if n >= self.state.crnd and n != slot.vrnd:
      self.state.crnd = n
      slot.vrnd = n
      slot.vval = v

      # Send learns to all
      for mac in self.state.ordered_nodes(self.mac):
        self.log.debug("LEARN n={} seq={} to {}".format(n, seqno, mac))
        self.send_learn(mac, n, seqno, v, self.lookup_port(mac))
    else:
      self.log.warning("On ACCEPT not accepted n={} seq={} crnd={}".format(
                       n, seqno, self.state.crnd))

    return EventHalt

  def lookup_port(self, mac):
    """Returns port MAC address is on or BROADCAST if not found."""
    if mac in self.switch.macports:
      return self.switch.macports[mac]
    else:
      if mac != self.mac:
        self.log.warning("Don't know which port {} is on, will broadcast".
            format(mac) + ", know these {}".format(self.switch.macports))
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

  def isleader(self):
    """Check if we are Paxos leader."""
    # NOTE: We have hardcoded that S1 is the leader.
    return self.name == "S1"

  def on_client(self, event, message):
    """On leader only: Process incoming CLIENT message."""
    if not self.isleader():
      self.log.warning("Got CLIENT message on non-leader, drop")
      # TODO: Forward to leader if we're not
      return EventHalt

    if not self.joined:
      self.log.critical("Refusing CLIENT packet until we've joined the " +
                        "Paxos network.")
      return EventHalt

    src, dst = self.get_ether_addrs(event)

    n = self.state.crnd
    seqno = self.leader.next_seqno()
    v = PaxosMessage.unpack_client(message)

    self.log.info("On CLIENT n={} seq={} {} -> {}".format(
                  n, self.leader.seqno, src, dst))

    # Send accepts to all
    for mac in self.state.ordered_nodes(self.mac):
      self.log.debug("ACCEPT n={} seq={} to {}".format(n, seqno, mac))
      self.send_accept(mac, n, seqno, v, self.lookup_port(mac))

    return EventHalt

  def send_accept(self, dst, n, seqno, v, port):
    payload = PaxosMessage.pack_accept(n, seqno, v)

    # Short-circuit messages to ourself
    if dst == self.mac:
      return self.on_accept(event=None, message=payload)
    else:
      return self.send_ethernet(src=self.mac,
                                dst=dst,
                                type=PaxosMessage.ACCEPT,
                                payload=payload,
                                output_port=port)

  def send_learn(self, dst, n, seqno, v, port):
    payload = PaxosMessage.pack_learn(n, seqno, v)

    # Short-circuit messages to ourself
    if dst == self.mac:
      return self.on_learn(event=None, message=payload)
    else:
      return self.send_ethernet(src=self.mac,
                                dst=dst,
                                type=PaxosMessage.LEARN,
                                payload=payload,
                                output_port=port)

  def on_join(self, event, message):
    node_id, mac_addr = PaxosMessage.unpack_join(message)
    mac = EthAddr(mac_addr)

    self.log.debug("JOIN <- {}".format(mac))

    # Only react on new nodes
    if mac not in self.state.N:
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
        self.log.debug("Broadcasting JOIN")
        dst = ETHER_BROADCAST
        port = of.OFPP_ALL
      else:
        self.log.debug("JOIN -> {}".format(mac))
        dst = mac_addr
        port = event.port

      self.send_join(dst, port)

  def send_join(self, dst, port):
    """Send a JOIN from this node to others."""
    src = EthAddr(self.mac).toRaw()
    payload = PaxosMessage.pack_join(self.state.n_id, src)
    return self.send_ethernet(src=src,
                             dst=dst,
                             type=PaxosMessage.JOIN,
                             payload=payload,
                             output_port=port)

  def get_ether_addrs(self, event):
    """Return (source, destination) MAC-addresses in event.
    If the event is None (typically, sent to ourself), return our own
    MAC-address."""
    if event is not None:
      return event.parsed.src, event.parsed.dst
    else:
      return self.mac, self.mac

  def on_learn(self, event, message):
    n, seqno, v = PaxosMessage.unpack_learn(message)
    src, dst = self.get_ether_addrs(event)

    if dst != self.mac:
      self.log.warning("LEARN from {} not to us".format(src))
      return EventHalt

    slot = self.state.slots.get_slot(seqno)
    self.log.info("On LEARN n={} seq={} from {} (learns {})".format(
      n, seqno, src, slot.votes))

    if slot.learned or n < slot.hrnd:
      return EventHalt

    # Initialize slot
    if n > slot.hrnd:
      slot.hrnd = n
      slot.reset_learns()

    if slot.hrnd == n:
      if src in slot.learns:
        # Already got one learn from this src with same round
        return EventHalt
      else:
        slot.update_learns(src)
        slot.value = v

    self.process_queue(n)
    return EventHalt

  def process_queue(self, n):
    """Processes messages in sequence, without gaps."""
    # TODO: This should really be called once in a while, not only on
    # learns, in case we have messages waiting to be delivered.
    for seqno, slot in self.state.slots.queue():
      assert(not self.state.slots.is_processed(n, seqno))

      if self.process_message(n, seqno, slot.value):
        self.state.slots.set_processed(n, seqno)
      else:
        break

  def process_message(self, n, seqno, v):
    """Act on a Paxos value that reached consensus.
    Returns True if message was processed."""

    # This is a raw Ethernet packet
    eth = pkt.ethernet(raw=v)

    self.log.info("PROCESS n=%d seq=%d, packet %s->%s type=0x%04x" % (
      n, seqno, eth.src, eth.dst, eth.type))

    # Known destination port? Forward it then.
    # TODO / NOTE: We need to discern between HOSTS and WAN here...
    #              We don't have a total map of the network...
    if eth.dst in self.switch.macports:
      # Don't forward to another Paxos switch
      if eth.dst not in self.paxos_ports:
        port = self.switch.macports[eth.dst]
        self.log.debug("PROCESS n={} seq={}, forward to port {}".format(
          n, seqno, port))

        # TODO: Update ETHER and IP DST for each host, and send to them.
        #       Then we don't need the two else-clauses below
        m = of.ofp_packet_out(data=eth)
        m.actions.append(of.ofp_action_output(port=port))
        self.connection.send(m)
        return True
      else:
        self.log.warning("Will not forward to other Paxos nets, drop")
        # If we change dst addresses, this will never happen
        return False
    else:
      self.log.warning("PROCESS: Unknown destination {}, postponed".format(
        eth.src, eth.dst))

      # Return false so we have a chance to process this message later, when
      # we know the destination.  Note that this later processing will
      # currently only be fired when we receive LEARNs.  We could create a
      # worker thread to pump the queue, but testing shows that usually
      # things resolve by itself (e.g, TCP may fire a retry).
      return False

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
          self.log.debug("Joined Paxos network of {} nodes".format(
            len(self.state.N)))
          break
        src = self.mac
        self.log.debug("Joining Paxos network, need {} more nodes".format(
          nodes_needed))
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

  # Instruct nexus to send FULL packets to controllers (will slow down
  # everything!)
  core.openflow.miss_send_len = 65535
  log.debug("Setting core.openflow.miss_send_len to {}".format(
    core.openflow.miss_send_len))

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
