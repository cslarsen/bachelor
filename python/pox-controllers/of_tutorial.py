# Copyright 2012 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This POX controller is a solution (correct also, I hope?) for the OpenFlow
tutorial.

It acted as a simple hub, but has been modified to act like an L2 learning
switch.

To use this, start up the POX controller with:

    $ ./pox.py log.level --DEBUG misc.of_tutorial

Then start mininet with

    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote

Then, when mininet and the controller are connected, ping all nodes:

    mininet> pingall

"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()



class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the [OpenFlow] connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """

    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).

  def learn_mac_port(self, mac, port):
    """Learn that a given MAC address is on the given switch PORT."""
    if not mac in self.mac_to_port:
      self.mac_to_port[mac] = port
      log.debug("Learned that {} is on port {}".format(mac, port))

      # TODO: Now that we've learned that, I think we could add a flow rule
      # that says to just forward all data going to MAC to the port PORT.

  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """
    # Learn the port for the source MAC
    self.learn_mac_port(packet.src, packet_in.in_port)

    # Do we know which ports both source and destination are on?
    if packet.dst in self.mac_to_port:
      dest_port = self.mac_to_port[packet.dst]

      # NOTE: I get more of these messages than I thought I should. I think
      # we get them for ARP messages as well as ICMP, i.e. for *everything*.
      # Would be nice to log what kind of packets we get to see the
      # difference.
      log.debug("Adding flow {}.{} -> {}.{}".
          format(packet.src, self.mac_to_port[packet.src],
                 packet.dst, self.mac_to_port[packet.dst]))

      ## Set fields to match received packet
      msg = of.ofp_flow_mod()
      msg.idle_timeout = 10
      msg.hard_timeout = 30

      # What to match on
      msg.match = of.ofp_match.from_packet(packet)
      msg.match.in_port = packet_in.in_port

      # Details on the stuff below can be read at
      # http://archive.openflow.org/wk/index.php/OpenFlow_Tutorial#Sending_OpenFlow_messages_with_POX

      # If we get a match with the given source and destination MAC
      # addresses, add an entry in the flow table that can automatically
      # route for us
      msg.match.dl_dst = packet.dst # match FROM this MAC address
      msg.match.dl_src = packet.src # match TO this MAC address

      # Optional; without it, it seems not to match on stuff it's seen
      # before (TODO: Find out why this should be here)
      msg.buffer_id = packet_in.buffer_id

      # REQUIRED; nothing will work without it (TODO: Find out why)
      msg.data = packet_in

      # Action for this rule is to SEND the data to the destination port
      msg.actions.append(of.ofp_action_output(port = dest_port))

      # Send the new flow rule to the switch
      self.connection.send(msg)

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(packet_in, of.OFPP_ALL)


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    #self.act_like_hub(packet, packet_in)
    self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
