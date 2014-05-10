"""
Contains stuff for working with Paxos messages.
"""

from struct import pack, unpack

from asserts import assert_u32
from limits import UINT32_MAX

ENABLE_ZLIB = False

class PaxosMessage(object):
  """Interface for creating Paxos-specific messages."""

  # Ethernet type identifiers for Paxos messages as unsigned 16-bit
  # integers.  They can be anything larger than 0x0600 (per the standard).
  #
  # We use bitfields so that we can potentially combine several messages.
  # For instance, it is customary to combine ACCEPT+LEARN in one message.
  #
  # Not all values need this, so we could leave some space for even more
  # message types.
  #
  JOIN    = 0x7A00
  ACCEPT  = 0x7A01
  LEARN   = 0x7A02
  TRUST   = 0x7A04
  PROMISE = 0x7A08
  PREPARE = 0x7A20
  CLIENT  = 0x7A40

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

  @staticmethod
  def pack_accept(crnd, seqno, cval):
    """Creates a PAXOS ACCEPT message."""
    assert_u32(crnd)
    assert_u32(seqno)
    return pack("!I", crnd) + pack("!I", seqno) + cval

  @staticmethod
  def unpack_accept(payload):
    """Unpacks a PAXOS ACCEPT message."""
    assert(isinstance(payload, str) and len(payload) >= 8)
    n = unpack("!I", payload[0:4])[0]
    s = unpack("!I", payload[4:8])[0]
    v = payload[8:]
    return n, s, v

  @staticmethod
  def pack_learn(n, seqno):
    """Creates a PAXOS LEARN message."""
    # Almost same structure as ACCEPT
    assert_u32(n)
    assert_u32(seqno)
    return pack("!I", n) + pack("!I", seqno)

  @staticmethod
  def unpack_learn(payload):
    """Unpacks a PAXOS LEARN message. """
    # Almost same structure as ACCEPT
    assert(isinstance(payload, str) and len(payload) == 8)
    n = unpack("!I", payload[0:4])[0]
    s = unpack("!I", payload[4:8])[0]
    return n, s

  @staticmethod
  def pack_client(payload):
    """Creates a PAXOS CLIENT message.

    Here we could to stuff like zlib-compress. I've tried it, and it works,
    but it's not part of the thesis. Just shows how easy it is to try out
    new stuff.

    However, to ease development, we add placeholders for two 32-bit
    unsigned integers, so we can rebroadcast the packet with parameters when
    the Paxos leader gets a PAXOS CLIENT message.
    """
    return pack("!I", 0) + pack("!I", 0) + payload

  @staticmethod
  def unpack_client(payload):
    """Extracts data in payload."""
    assert(isinstance(payload, str) and len(payload) >= 8)
    return payload[8:]
