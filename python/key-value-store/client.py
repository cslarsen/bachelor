"""
A key-value store client
"""

import time

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
  print("Waiting for PING reply on {}:{}".format(ip, port))
  print("PING reply: {}".format(client.ping()))

  key = "counter"
  value = 0

  while True:
    client.put(key, value)
    value += 1

    print("server count is {}".format(client.get(key)))
    time.sleep(1)
