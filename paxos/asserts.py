"""
Miscellenaous functions for assertions.
"""

def assert_int(n):
  assert(isinstance(n, int))

def assert_uint(n, max_int):
  assert_int(n)
  assert(0 <= n <= max_int)

def assert_u32(n):
  assert_uint(n, (2<<31)-1)

def assert_u16(n):
  assert_uint(n, (2<<15)-1)

def assert_u8(n):
  assert_uint(n, (2<<7)-1)
