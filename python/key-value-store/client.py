"""
A key-value store client
"""

import socket
import sys
import time

import log
import message
import udp

def _write(message):
  """Write a message to stdout and flush it."""
  sys.stdout.write(message)
  sys.stdout.flush()

class Client(object):
  def __init__(self, ip, port, timeout=1, print_resends=True):
    """
    Args:
      ip: IP address of server
      port: Port on server
    """
    self.udp = udp.UDP(remote_ip=ip, remote_port=port)
    self.udp.timeout(timeout)
    self.print_resends = print_resends

  def get(self, key):
    """Fetch a value form the server."""
    # Try until we get a reply
    while True:
      try:
        reply, _ = self.udp.sendrecv(message.get(key))
        return message.parse_response(reply)
      except socket.timeout:
        if self.print_resends:
          _write(".")
        continue
      except Exception, e:
        raise e

  def put(self, key, value):
    """PUT a key/value pair."""
    # Try until we get a reply
    while True:
      try:
        reply, _ = self.udp.sendrecv(message.put(key, value))
        return message.parse_response(reply)
      except socket.timeout:
        if self.print_resends:
          _write(".")
        continue
      except Exception, e:
        raise e

  def ping(self):
    """Blocking PING (waits for reply)"""

    # Will resend until we get a reply
    while True:
      try:
        reply, _ = self.udp.sendrecv(message.ping())
        return message.parse_response(reply)
      except socket.timeout:
        if self.print_resends:
          _write(".")
        continue
      except Exception, e:
        raise e

if __name__ == "__main__":
  ip = "0.0.0.0"
  port = 1234
  client = Client(ip, port)
  log.info("Waiting for PING reply on ", ip, ":", port)
  log.info("PING reply from server: ", client.ping())

  key = "counter"
  value = 0

  while True:
    server_value = client.get(key)

    """
    TODO: In normal operation, we want to clients and a monotonically
    increasing server value. But in the face of packet loss, or if one of
    the servers goes down or experiences packet loss, we want to make sure
    we introduce some errors. So make an algorithm HERE that introduces
    errors on the server part. (what we want is two overlapping PUTs from
    two different clients, both clients increase the server value by one,
    but if they overlap we'll get non-increasing values.. or increments more
    than one.
    """
    if server_value != value:
      log.warn("server value {} != our value {}, resetting".
          format(server_value, value))
    client.put(key, value+1)
    log.info("our count=", value, " server count=", server_value)
    value += 1
    time.sleep(1)
