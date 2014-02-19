from pickle import (dumps, loads)
from socket import timeout
import sys

from communication import UDP
import log

class PaxosSender(object):
  """A class for sending Paxos messages."""
  def __init__(self, transport):
    self.transport = transport

  def _send(self, to, data):
    """Serialize and send message, returning number of bytes sent."""
    log.info("Sending {} from {} to {}".format(
      data, self.transport.address, to))
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
    log.debug("receive sender={} data={}".format(sender, loads(data)))

    message = loads(data)
    command = message[0]
    args = message[1:]

    log.debug("{} from {}".format(command, sender))

    if command in self.dispatch:
      on_function = self.dispatch[command]
      on_function(sender, *args)
    else:
      self.on_unknown(sender, message)

  def on_unknown(self, sender, message):
    """Called when an unknown command was received."""
    log.warn("{} Unimplemented on_unknown({}, {})".format(
      self.transport.address, sender, message))

  def on_prepare(self, sender, crnd):
    log.warn("{} Unimplemented on_prepare({}, crnd={})".format(
      self.transport.address, sender, crnd))

  def on_accept(self, sender, crnd, cval):
    log.warn("{} Unimplemented on_accept({}, crnd={}, cval={})".format(
      self.transport.address, sender, crnd, cval))

  def on_trust(self, sender, c):
    log.warn("{} Unimplemented on_trust({}, c={})".format(
      self.transport.address, sender, c))

  def on_promise(self, sender, rnd, vrnd, vval):
    log.warn("{} Unimplemented on_promise({}, rnd={}, vrnd={}, vval={})".
      format(self.transport.address, sender, rnd, vrnd, vval))

  def on_learn(self, sender, n, v):
    log.warn("{} Unimplemented on_learn({}, n={}, v={})".format(
      self.transport.address, sender, n, v))

class PaxosRole(PaxosSender, PaxosReceiver):
  """Base class for a specific Paxos role."""
  def __init__(self, name, ip='', port=0):
    self.udp = UDP(ip, port)
    self.name = name
    self.stop = None
    PaxosSender.__init__(self, self.udp)
    PaxosReceiver.__init__(self, self.udp)

  def __repr__(self):
    return "<PaxosRole {} {}:{}>".format(self.name, self.udp.ip,
        self.udp.port)

  def loop(self):
    """Start handling messages in a loop."""
    log.info("{} listening on {}:{}".format(self.name, self.udp.ip, self.udp.port))
    self.stop = False
    while not self.stop:
      try:
        self.receive()
      except timeout:
        sys.stdout.write(".")
        sys.stdout.flush()
    log.info("{} STOPPED listening on {}:{}".format(self.name, self.udp.ip, self.udp.port))
