"""
Miscellenaous functions for assertions.
"""

import limits

def assert_int(n):
  assert(isinstance(n, int))

def assert_uint(n, max_int):
  assert_int(n)
  assert(0 <= n <= max_int)

def assert_u32(n):
  assert_uint(n, limits.UINT32_MAX)

def assert_u16(n):
  assert_uint(n, limits.UINT16_MAX)

def assert_u8(n):
  assert_uint(n, limits.UINT8_MAX)
