from pickle import (dumps, loads)
from socket import (AF_INET, SOCK_DGRAM, socket, timeout)
import sys

import log

class UDP(object):
  """A class for sending messages on the network.

  Args:
    ip:   Bind to given IP-address.
    port: Bind to given port.
  """
  def __init__(self, ip='', port=0, timeout=1):
    self.socket = socket(AF_INET, SOCK_DGRAM)
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

class PaxosSender(object):
  """A class for sending Paxos messages."""
  def __init__(self, transport):
    self.transport = transport

  def _send(self, to, data):
    """Serialize and send message, returning number of bytes sent."""
    log.info("Sending {} to {}".format(data, to))
    return self.transport.sendto(to, dumps(data))

  def prepare(self, to, crnd):
    return self._send(to, ("prepare", crnd))

  def accept(self, to, crnd, cval):
    return self._send(to, ("accept", crnd, cval))

  def trust(self, to, c):
    return self._send(to, ("trust", c))

  def promise(self, to, rnd, vrnd, vval):
    return self._send(to, ("promise", rnd, vrnd, vval))

  def learn(self, to, n, v):
    return self._send(to, ("learn", n, v))

class PaxosReceiver(object):
  """A class for receiving Paxos messages."""
  def __init__(self, transport):
    self.transport = transport
    self.dispatch = {"prepare": self.on_prepare,
                     "accept": self.on_accept,
                     "trust": self.on_trust,
                     "promise": self.on_promise,
                     "learn": self.on_learn}

  def receive(self):
    """Wait until we receive one message from the network."""
    data, sender = self.transport.recvfrom()
    log.debug("receive sender={} data='{}'".format(sender, loads(data)))

    message = loads(data)
    command = message[0]
    args = message[1:]

    log.info("{} from {}".format(command, sender))

    if command in self.dispatch:
      on_function = self.dispatch[command]
      on_function(sender, *args)
    else:
      self.on_unknown(sender, message)

  def on_unknown(self, sender, message):
    """Called when an unknown command was received."""
    raise NotImplementedError()

  def on_prepare(self, sender, crnd):
    raise NotImplementedError()

  def on_accept(self, sender, crnd, cval):
    raise NotImplementedError()

  def on_trust(self, sender, c):
    raise NotImplementedError()

  def on_promise(self, sender, rnd, vrnd, vval):
    raise NotImplementedError()

  def on_learn(self, sender, n, v):
    raise NotImplementedError()

class PaxosRole(PaxosSender, PaxosReceiver):
  """Base class for a specific Paxos role."""
  def __init__(self, name, ip='', port=0):
    self.udp = UDP(ip, port)
    self.name = name
    PaxosSender.__init__(self, self.udp)
    PaxosReceiver.__init__(self, self.udp)

  def loop(self):
    """Start handling messages in a loop."""
    log.info("{} listening on {}:{}".format(self.name, self.udp.ip, self.udp.port))
    while True:
      try:
        self.receive()
      except timeout:
        sys.stdout.write(".")
        sys.stdout.flush()
