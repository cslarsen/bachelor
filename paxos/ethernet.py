"""
Miscellaneous functions for working with Ethernet.
"""

def str2mac(s):
  """Converts MAC address "aa:bb:cc:dd:ee:ff" to raw bytes."""
  assert(len(s) == len("aa:bb:cc:dd:ee:ff"))
  return "".join(map(chr, map(lambda s: int(s, base=16), s.split(":"))))

def mac2str(s):
  """Convert raw MAC bytes to string."""
  assert(len(s) == 6)
  return ":".join(map(lambda n: hex(ord(n))[2:], s))

def str2type(s):
  """Hexadecimal string to Ethernet type raw bytes (unsigned 16-bit)."""
  if s.startswith("0x"):
    n = int(s[2:], base=16)
  else:
    n = int(s)
  return chr(n >> 8) + chr(n & 0xFF)

def type2str(s):
  """Raw Ethernet bytes (string) to hexadecimal string-representation."""
  assert(isinstance(s, str) and len(s) == 2)
  h, l = map(ord, s)
  n = (h<<8) | l
  return "0x%04x" % n
