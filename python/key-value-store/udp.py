import pickle
import random
import socket

import log

class UDP(object):
  """An UDP wrapper that can act as a client or server."""
  def __init__(self,
               remote_ip=None,
               remote_port=None,
               bind_ip="0.0.0.0",
               bind_port=None,
               debug_unpickle=False):
    self.bind_ip = bind_ip
    self.bind_port = bind_port
    self.to_ip = remote_ip
    self.to_port = remote_port
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.debug_unpickle = debug_unpickle

    # No port specified? Bind to a random port.
    if self.bind_port is None:
      self.bind_random_port()
    else:
      self.bind()

  def timeout(self, timeout):
    self.sock.settimeout(timeout)

  def bind(self):
    self.sock.bind((self.bind_ip, self.bind_port))
    log.debug("Bound {}:{}".format(self.bind_ip, self.bind_port))

  def bind_random_port(self):
    """Binds to first free, random port."""
    while True:
      try:
        port = random.randint(1024, 65536)
        self.sock.bind((self.bind_ip, port))
        self.bind_port = port
        log.debug("Bound {}:{}".format(self.bind_ip, self.bind_port))
        break
      except socket.error:
        continue

  def send(self, data):
    """Sends an UDP message to predetermined IP and PORT.
    Returns number of bytes sent."""
    return self.sendto(self.to_ip, self.to_port, data)

  def sendto(self, ip, port, data):
    """Sends an UDP message to gven IP:PORT and returns number of bytes
    sent."""
    log.debug("UDP.sendto {}:{} length={}".format(ip, port, len(data)))
    if self.debug_unpickle:
      log.debug("  data '{}'".format(pickle.loads(data)))
    return self.sock.sendto(data, (ip, port))

  def recv(self, buffer_size=1024):
    """Receives message from given IP:PORT and returns message."""
    log.debug("UDP.recv on local {}:{} buffer_size={}".format(self.bind_ip,
      self.bind_port, buffer_size))
    data, (ip, port) = self.sock.recvfrom(buffer_size)

    log.debug("UDP.recv from {}:{} length={}".format(ip, port, len(data)))
    if self.debug_unpickle:
      log.debug("  data '{}'".format(pickle.loads(data)))
    return data, (ip, port)

  def recv_loop(self, buffer_size=1024):
    """Runs recv in loop and yields values."""
    while True:
      yield self.recv(buffer_size)

  def sendtorecv(self, ip, port, message, buffer_size=1024):
    """Send followed by receive. Returns message and sender."""
    self.sendto(ip, port, message)
    return self.recv(buffer_size)

  def sendrecv(self, message, buffer_size=1024):
    """Send to predetermined host, followed by receive."""
    return self.sendtorecv(self.to_ip, self.to_port, message, buffer_size)
