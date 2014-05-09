import random
import unittest

from pox.lib.addresses import EthAddr

from paxos.controller.paxosctrl import PaxosMessage

def random_u32():
  return random.randint(0, 0xFFFFFFFF)

def random_u8():
  return random.randint(0, 0xFF)

def random_str(length):
  return "".join(chr(random.randint(0,255)) for n in xrange(length))

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
    for _ in xrange(macs):
      mac = random_mac()
      for _ in xrange(ids):
        node_id = random_u32()
        test(node_id, mac.lower())
        test(node_id, mac.upper())
        test(node_id, mac)

    print("%d tests " % (ids*macs)),

  def test_accept(self):
    """Fuzzy-testing PaxosMessage.pack_accept and unpack_accept"""
    def test(n, seqno, v):
      p = PaxosMessage.pack_accept(n, seqno, v)
      self.assertIsNotNone(p)
      self.assertGreater(len(p), 7)
      u = PaxosMessage.unpack_accept(p)
      self.assertIsNotNone(u)
      self.assertEquals(len(u), 3)
      self.assertEquals(n, u[0])
      self.assertEquals(seqno, u[1])
      self.assertEquals(v, u[2])

    N = 15
    for _ in xrange(0, N):
      v = random_str(random.randint(0, (2<<15)-1))
      for _ in xrange(0, N):
        seqno = random_u32()
        for _ in xrange(0, N):
          n = random_u32()
          test(n, seqno, v)
    print("%d tests " % N**3),

  def test_learn(self):
    """Fuzzy-testing PaxosMessage.pack_learn and unpack_learn"""
    def test(n, seqno):
      p = PaxosMessage.pack_learn(n, seqno)
      self.assertIsNotNone(p)
      self.assertGreater(len(p), 7)
      u = PaxosMessage.unpack_learn(p)
      self.assertIsNotNone(u)
      self.assertEquals(len(u), 2)
      self.assertEquals(n, u[0])
      self.assertEquals(seqno, u[1])

    N = 90
    for i in xrange(0, N):
      n = random_u32()
      for j in xrange(0, N):
        seqno = random_u32()
        test(n, seqno)
    print("%d tests " % N**2),


if __name__ == "__main__":
  unittest.main(verbosity=2)
