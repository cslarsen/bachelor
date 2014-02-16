"""
A key-value store client
"""

import time

import log
import message
import udp

class Client(object):
  def __init__(self, ip, port):
    """
    Args:
      ip: IP address of server
      port: Port on server
    """
    self.ip = ip
    self.port = port

  def get(self, key):
    """Fetch a value form the server."""
    data = message.get(key)
    return message.parse_response(udp.sendrecv(ip, port, data))

  def put(self, key, value):
    """PUT a key/value pair."""
    data = message.put(key, value)
    return udp.sendrecv(ip, port, data)

  def ping(self):
    """Blocking PING (waits for reply)"""
    return message.parse_response(udp.sendrecv(ip, port, message.ping()))

if __name__ == "__main__":
  ip = "0.0.0.0"
  port = 1234
  client = Client(ip, port)
  log.info("Waiting for PING reply on ", ip, ":", port)
  log.info("PING reply from server: ", client.ping())

  key = "counter"
  value = 0

  while True:
    client.put(key, value)
    new_value = client.get(key)
    log.info("our count=", value, " server count=", new_value)
    if value != new_value:
      log.warn("setting our count to ", new_value)
    value = new_value + 1
    time.sleep(1)
