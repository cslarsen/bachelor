import socket

class UDP(object):
  """A class for sending messages on the network.

  Args:
    ip:   Bind to given IP-address.
    port: Bind to given port.
  """
  def __init__(self, ip='', port=0, timeout=1):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable us to reuse address even if it's in TIME_WAIT (e.g. you just
    # crashed your program and restarted it)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    self.socket.bind((ip, port))
    self.timeout = timeout

  def sendto(self, (ip, port), data):
    """Sends data to given host and returns number of bytes sent."""
    return self.socket.sendto(data, (ip, port))

  def recvfrom(self, buffer_size=1024):
    """Blocks, waiting to receive data from bound address."""
    return self.socket.recvfrom(buffer_size)

  @property
  def timeout(self):
    return self.socket.gettimeout()

  def local_ip(self, destination):
    """Returns the local IP-address that will be used when sending to
    destination (IP, port)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(destination)

    # only return IP address as the port changes between each sendto, unless
    # we actually keep the connection open.
    ip = s.getsockname()[0]

    s.close()
    return ip

  @timeout.setter
  def timeout(self, timeout):
    self.socket.settimeout(timeout)

  @property
  def ip(self):
    """Returns local IP address."""
    ip, _ = self.socket.getsockname()
    return ip

  @property
  def port(self):
    """Returns local port number."""
    _, port = self.socket.getsockname()
    return port

  @property
  def address(self):
    """Returns (ip, port)"""
    return self.socket.getsockname()
