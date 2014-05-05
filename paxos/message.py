"""
Contains stuff for working with Paxos messages.
"""

from struct import pack, unpack

from asserts import assert_u32

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
