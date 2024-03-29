"""
An L2 learning switch.

We use this for benchmarking.
"""

import os
import sys
import pprint

from pox.core import core
from pox.lib.addresses import EthAddr
from pox.lib.util import dpid_to_str
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

class BaselineController(object):
  """An L2 learning switch to be used with benchmarking."""

  def __init__(self,
               connection,
               priority=1,
               quit_on_connection_down=False,
               add_flows=True,
               name_prefix="Switch-",
               name_suffix=True,
               learn_ip_addresses=False,
               clear_flows_on_startup=False):

    self.add_flows = add_flows
    self.connection = connection
    self.quit_on_connection_down = quit_on_connection_down
    self.learn_ip_addresses = learn_ip_addresses

    # Map of MAC address to PORT
    self.macports = {}

    # Map of MAC address to IP address
    self.macip = {}

    # Defaults
    self.idle_timeout = 3600
    self.hard_timeout = 3600

    # Settings for logging, set to "" to disable or a character to enable.
    self.log_broadcast = "b" #"b"
    self.log_flow = "" #"F"
    self.log_forward = "f" #"f"
    self.log_incoming = "i" #"."
    self.log_learn = "l" #"L"
    self.log_miss = "."

    # Full-text logs, set to False to disable
    # TODO: Just log these as DEBUG-level logs, then we can turn off at
    # will.
    self.log_broadcast_full = False
    self.log_flow_full = True
    self.log_incoming_full = False
    self.log_learn_full = True
    self.log_miss_full = False

    if name_suffix:
      name = "{}{}".format(name_prefix, connection.ID)
    else:
      name = "{}".format(name_prefix)

    self.log = core.getLogger(name)
    self.log.info("{} controlling connection id {}, DPID {}".format(
      self.__class__.__name__, connection.ID, dpid_to_str(connection.dpid)))
    self.log.debug("idle timeout={}, hard timeout={}".format(
      self.idle_timeout, self.hard_timeout))
    self.log.debug("Add flows: {}".format(self.add_flows))

    # Produce a nice legend of symbols used in log
    def legend(char, descr):
      if len(char) > 0:
        return "\n  '%s' %s" % (char, descr)
      return ""
    descr = ""
    descr += legend(self.log_flow, "when flows are installed")
    descr += legend(self.log_broadcast, "when controller broadcasts")
    descr += legend(self.log_forward, "when controller forwards")
    descr += legend(self.log_incoming, "when controller receives a packet")
    descr += legend(self.log_learn, "when we learn a MAC's port")
    descr += legend(self.log_miss, "for MAC-port table misses")
    if len(descr) > 0:
      descr = "Symbols used for logging events:" + descr
      self.log.info(descr)

    if clear_flows_on_startup:
      self.log.debug("Clearing flow table on startup")
      self.clear_flowtable()

    if self.add_flows:

      self.log.info("Adding forwarding rule for Ethernet broadcasts")
      # Add a rule so that the switch doesn't upcall Ethernet broadcasts,
      # but handles it itself.
      self.add_forward_flow(None, EthAddr("ff:ff:ff:ff:ff:ff"), of.OFPP_ALL)

    # Listen for events from the switch
    self.connection.addListeners(self, priority=priority)

    # When connection goes down, we need to reset our MAC table
    self.connection.addListenerByName("ConnectionDown", self.connectionDown)

  def connectionDown(self, event):
    """Called when connection to switch goes down."""
    self.log.info("Connection to switch has gone down")
    self.clear_macports()
    self.clear_flowtable()
    if self.quit_on_connection_down:
      self.log.info("Telling POX to shut down")
      core.quit()

    # FUN FACT:
    # If mininet ping test starts and this controller stops, if we don't
    # clear out a fully populated flow table, then mininet's switch will
    # continue working because it can handle stuff on its own with its flow
    # table entries.

  def clear_macports(self):
    """Clears out learned MAC ports."""
    self.log.debug("Clearing out MAC->PORT table (flushing {} entries)".
        format(len(self.macports)))
    self.macports = {}

  def clear_flowtable(self):
    """ Removes all flow table entries on switch."""
    # Taken from https://openflow.stanford.edu/display/ONL/POX+Wiki#POXWiki-Example%3AClearingtablesonallswitches

    # create ofp_flow_mod message to delete all flows
    # (note that flow_mods match all flows by default)
    msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)

    # iterate over all connected switches and delete all their flows
    #for connection in core.openflow.connections: # _connections.values() before betta
    self.connection.send(msg)
    self.log.debug("Clearing all flows from %s." % (dpid_to_str(self.connection.dpid),))

  def drop(self, event):
    """Instructs switch to drop packet from in event."""
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    self.connection.send(msg)

  def dotlog(self, char):
    """Print a character to stdout if set."""
    if char is not None and len(char) > 0:
      sys.stdout.write(char)
      sys.stdout.flush()

  def broadcast(self, packet_in):
    """Forward packet to all nodes."""
    self.dotlog(self.log_broadcast)
    self.forward(packet_in, of.OFPP_ALL)

  def forward(self, packet_in, port):
     """Instructs switch to forward the packet to the given port."""
     self.dotlog(self.log_forward)
     msg = of.ofp_packet_out()
     msg.data = packet_in
     msg.actions.append(of.ofp_action_output(port=port))
     self.connection.send(msg)

  def learn_port(self, mac, port):
    """Learns which port a MAC address is located."""
    if mac not in self.macports:
      self.macports[mac] = port
      self.dotlog(self.log_learn)
      if self.log_learn_full:
        self.log.debug("Learned that {} is on port {} ({} entries)".
            format(mac, port, len(self.macports)))

  def learn_ip(self, mac, ip):
    """Learns which IP-address a MAC-address is bound to."""
    # NOTE: Some switches change the MAC source during hops, so perhaps it
    # would be better to just store a map of IP-addresses-to-port-numbers
    # instead? (TODO)
    if mac not in self.macip:
      self.macip[mac] = ip
      self.log.debug("Learned that MAC {} has IP address {}".format(
        mac, ip))

  def add_forward_flow(self, from_mac, to_mac, forward_to_port):
    """Install flow table entry

    Args:
      destination_mac: Match on this destination MAC address
      forward_to_port: If there's a match, forward to this port.
    """
    if self.log_flow_full:
      self.log.debug("Adding forwarding flow: %s->%s.%i" %
        (from_mac, to_mac, forward_to_port))

    self.dotlog(self.log_flow)

    # New flow message
    msg = of.ofp_flow_mod()

    # Set flow timeouts
    msg.idle_timeout = self.idle_timeout
    msg.hard_timeout = self.hard_timeout

    # Previously: Match on as many fields as possible (from L2 POX example)
    # msg.match = of.ofp_match.from_packet(packet, event.port)
    # Now: Only add flow if both ports are known, lock to these two
    #      (see notes below for a detailed explanation)

    # If ...
    #
    if from_mac is not None: # Allow for wildcard by using from_mac=None
      msg.match.dl_src = from_mac
    #
    msg.match.dl_dst = to_mac
    #
    # Then ...
    #
    msg.actions.append(of.ofp_action_output(port=forward_to_port))

    # Send flow rule to switch
    self.connection.send(msg)

  def _handle_PacketIn(self, event):
    """Handle incoming packet from switch."""

    # Fetch packet --- note that we usually just get the first 128 bytes.
    packet_in = event.ofp
    packet = event.parsed

    if self.log_incoming_full:
      self.log.debug("Got a packet: packet={}".format(packet))
    self.dotlog(self.log_incoming)

    # Learn which port the sender is connected to
    self.learn_port(packet.src, event.port)

    # Should we track IP-addresses?
    if self.learn_ip_addresses:
      # If this is an IP-packet, extract source IP-address
      ip = packet.find(pkt.ipv4)
      if ip:
        self.learn_ip(packet.src, ip.srcip)

    # Do we know the destination port?
    if not packet.dst in self.macports:
      if self.log_miss_full:
        self.log.debug(
          "Don't know which port {} is on for {}, rebroadcasting".format(
            packet.dst, packet))

      self.dotlog(self.log_miss)

      if self.log_broadcast_full:
        self.log.debug("Rebroadcasting MAC %s.%d -> %s" % (
          packet.src, self.macports[packet.src], packet.dst))

      self.broadcast(packet_in)
    elif not self.add_flows:
      # If we're not using flows to do the forwarding, we need to do it
      # manually here.
      self.forward(packet_in, self.macports[packet.dst])
    else:
      # Only add flows when we know BOTH ports, or else we will NEVER
      # install certain flows.
      #
      # E.g., if h1 pings h9, all switches will learn h1's port, but when h9
      # replies to h1, the pings will go through the flow tables, leaving
      # the controllers with no clue about h9's port.
      #
      # Secondly, we can't install SEPARATE flows for each "if dst=x,
      # forward to port=y", because that would lead to the same situation.
      # If we have flows to forward to h1 and h9, then when any of them ping
      # h2, we will not learn h2's port, because the answer from h2 (along
      # with its MAC and port) will bypass the controllers.
      self.add_forward_flow(packet.src, packet.dst, self.macports[packet.dst])
      self.add_forward_flow(packet.dst, packet.src, self.macports[packet.src])

      # Forward the packet manually this one time
      self.forward(packet_in, self.macports[packet.dst])

  def mac_to_port(self, mac, default=False):
    """Returns port number for MAC-address if known, `default` if not."""
    if mac in self.macports:
      return self.macports[mac]
    else:
      return default

  def port_to_mac(self, port, default=False):
    """Return all MAC-addresses we know on the given port."""
    if port in self.macports.values():
      return [m for (m,p) in self.macports.items() if p==port]
    else:
      return default

  def mac_to_ip(self, mac, default=False):
    """Returns IP-address for MAC if known, `default` otherwise."""
    if mac in self.macip:
      return self.macip[mac]
    else:
      return default

  def ip_to_mac(self, ip, default=False):
    """Returns MAC-address associated with IP-address if known, `default`
    otherwise."""
    if ip in self.macip.values():
      return [m for (m,i) in self.macip.items() if i==ip][0]
    else:
      return default

  def ip_to_port(self, ip, default=False):
    """Returns port-number associated with IP-address if known,
    `default` otherwise."""
    mac = self.ip_to_mac(ip, default=False)
    if mac:
      return self.mac_to_port(mac, default=default)
    else:
      return default


def launch():
  """Starts the controller."""
  log = core.getLogger()
  Controller = BaselineController

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
