from paxos.controller.paxosctrl import PaxosMessage
from pox.lib.addresses import EthAddr
import random
import unittest

def random_u32():
  return random.randint(0, 0xFFFFFFFF)

def random_u8():
  return random.randint(0, 0xFF)

def random_mac():
  return ":".join(map(lambda n: "%02x" % n,
                      [random_u8(),
                       random_u8(),
                       random_u8(),
                       random_u8(),
                       random_u8(),
                       random_u8()]))

class TestPaxosController(unittest.TestCase):
  def test_create_join(self):
    """Fuzzy-testing PaxosMessage.pack_join and unpack_join"""

    def test(n, mac):
      """Perform detailed tests on packing."""
      mac = EthAddr(mac).toRaw()
      n_packed = "".join(
                    map(chr, [n>>24, n>>16 & 0xFF, n>>8 & 0xFF, n & 0xFF]))
      packed = PaxosMessage.pack_join(n, mac)
      unpacked = PaxosMessage.unpack_join(packed)

      # Convert to wire format and back again
      self.assertEqual((n, mac), unpacked)

      # Check wire-format
      self.assertEqual(len(packed), 6+4)
      self.assertEqual(packed[0:4], n_packed)
      self.assertEqual(packed[4:10], mac)

      # In one go
      self.assertEqual((n, mac),
                       PaxosMessage.unpack_join(
                         PaxosMessage.pack_join(n, mac)))

    # Fuzzy-test function with random node ids and mac addresses
    ids, macs = 66, 66
    for _ in xrange(ids):
      node_id = random_u32()
      for _ in xrange(macs):
        mac = random_mac()
        test(node_id, mac.lower())
        test(node_id, mac.upper())
        test(node_id, mac)

    print("%d tests" % (ids*macs))

if __name__ == "__main__":
  unittest.main(verbosity=2)
