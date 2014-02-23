from pickle import (dumps, loads)
from socket import timeout
import sys

from communication import UDP
import log

class PaxosSender(object):
  """A class for sending Paxos messages."""
  def __init__(self, transport, get_id=lambda x: x):
    """
    Args:
      transport: A transport mechanism for sending and receiving messages.
                 Must provide send and recv methods and ip and port
                 properties, at the very least. Use e.g. UDP here.
      get_id:    Looks up ID based on an IP-address. Default is to show
                 IP-address.
    """
    self.transport = transport
    self.get_id = get_id

  def _send(self, to, data):
    """Serialize and send message, returning number of bytes sent."""
    src = self.id
    dst = self.get_id(to)

    log.debug("{}->{}: {}{}".format(
      src,
      dst,
      data[0],
      data[1:]))

    return self.transport.sendto(to, dumps(data))

  def prepare(self, to, crnd):
    """Sends a PREPARE message."""
    return self._send(to, ("prepare", crnd))

  def accept(self, to, crnd, cval):
    """Sends an ACCEPT message."""
    return self._send(to, ("accept", crnd, cval))

  def trust(self, to, c):
    """Sends a TRUST(c) message."""
    return self._send(to, ("trust", c))

  def promise(self, to, rnd, vrnd, vval):
    """Sends a PROMISE message."""
    return self._send(to, ("promise", rnd, vrnd, vval))

  def learn(self, to, rnd, vval):
    """Sends a LEARN message."""
    return self._send(to, ("learn", rnd, vval))

  def ping(self, to, cookie):
    """Sends a PING message."""
    return self._send(to, ("ping", cookie))

class PaxosReceiver(object):
  """A class for receiving Paxos messages."""
  def __init__(self, transport):
    """
    Args:
      transport: A transport mechanism for sending and receiving messages.
                 Must provide send and recv methods and ip and port
                 properties, at the very least. Use e.g. UDP here.
    """
    self.transport = transport

    # Set up a dispatch table that will pass on command arguments to the
    # given methods.
    self.dispatch = {"prepare": self.on_prepare,
                     "accept": self.on_accept,
                     "trust": self.on_trust,
                     "promise": self.on_promise,
                     "learn": self.on_learn,
                     "ping": self.on_ping,
                     "ping-reply": self.on_ping_reply}

  def receive(self):
    """Wait until we receive one message from the network and dispatch it
    internally.

    If this times out (see the timeout property) you will get a
    socket.timeout exception."""

    data, sender = self.transport.recvfrom()
    log.debug("receive sender={0} data={1}".format(sender, loads(data)))

    message = loads(data)
    command = message[0]
    args = message[1:]

    log.debug("{0} from {1}".format(command, sender))

    if command in self.dispatch:
      on_function = self.dispatch[command]
      on_function(sender, *args)
    else:
      self.on_unknown(sender, message)

    # For pump(), return the message
    return message

  def on_unknown(self, sender, message):
    """Called when an unknown command was received."""
    log.warn("{0} Unimplemented on_unknown({1}, {2})".format(
      self.transport.address, sender, message))

  def on_prepare(self, sender, crnd):
    """Called when PREPARE is received."""
    log.warn("{0} Unimplemented on_prepare({1}, crnd={2})".format(
      self.transport.address, sender, crnd))

  def on_accept(self, sender, crnd, cval):
    """Called when an ACCEPT is received."""
    log.warn("{0} Unimplemented on_accept({1}, crnd={2}, cval={3})".format(
      self.transport.address, sender, crnd, cval))

  def on_trust(self, sender, c):
    """Called when a TRUST is received."""
    log.warn("{0} Unimplemented on_trust({1}, c={2})".format(
      self.transport.address, sender, c))

  def on_promise(self, sender, rnd, vrnd, vval):
    """Called when a PROMISE is received."""
    log.warn("{0} Unimplemented on_promise({1}, rnd={2}, vrnd={3}, vval={3})".
      format(self.transport.address, sender, rnd, vrnd, vval))

  def on_learn(self, sender, rnd, vval):
    """Called when a LEARN is received."""
    log.warn("{0} Unimplemented on_learn({1}, rnd={2}, vval={3})".format(
      self.transport.address, sender, rnd, vval))

  def on_ping(self, sender, cookie):
    src = self.nodes.get_id(sender)
    log.debug("{}<-{} on_ping(id={}, cookie={})".format(
      self.id, src, src, cookie))
    log.debug("{}->{} ping(cookie={})".format(
      self.id, src, cookie))
    return self.transport.sendto(sender, dumps(("ping-reply", cookie)))

  def on_ping_reply(self, sender, cookie):
    src = self.nodes.get_id(sender)
    log.debug("{}<-{} on_ping_reply(cookie={})".format(self.id, src, cookie))

class PaxosRole(PaxosSender, PaxosReceiver):
  """Base class for a specific Paxos role. Proposers and Acceptors must
  subclass this."""

  def __init__(self, name, ip='', port=0, get_id=lambda x: x):
    """
    Args:
      name: Name of this role (e.g. "Acceptor" or "Proposer")
      ip:   IP address to listen for messages. Use the default value to
            listen to let the system decide (usually means we listen on local
            host).
      port: PORT number to listen for messages. Leave at default value to
            automatically select a free port.
      get_id: Translates IP address to ID. Default is to show IP-address.
    """
    self.name = name
    self.udp = UDP(ip, port)
    self.get_id = get_id
    self.stop = None # Flag used to control loop
    PaxosSender.__init__(self, self.udp, get_id)
    PaxosReceiver.__init__(self, self.udp)

  def __repr__(self):
    """Returns a string representation for this object."""
    return "<PaxosRole {0} {1}:{2}>".format(self.name, self.udp.ip,
        self.udp.port)

  @property
  def address(self):
    return self.udp.address

  def pump(self):
    """Block until we've gotten one message, run the handler and return the
    message."""
    while True:
      try:
        return self.receive()
      except timeout:
        char = "."
        if self.name == "Proposer": char = "P"
        elif self.name == "Acceptor": char = "A"
        elif self.name == "Learner": char = "L"
        sys.stdout.write(char)
        sys.stdout.flush()
      except KeyboardInterrupt:
        return
      except Exception, e:
        log.exception(e)
        return

  def loop(self):
    """Start receiving and handling messages in a loop."""

    # In case we've been signaled to stop BEFORE even starting the loop
    if self.stop != None:
      return

    log.info("Node {}: {} listening on {}:{}".format(self.id, self.name,
      self.udp.ip, self.udp.port))
    self.stop = False
    while not self.stop:
      try:
        self.receive()
      except timeout:
        char = "."
        if self.name == "Proposer": char = "P"
        elif self.name == "Acceptor": char = "A"
        elif self.name == "Learner": char = "L"
        sys.stdout.write(char)
        sys.stdout.flush()
      except KeyboardInterrupt:
        self.stop = True
      except Exception, e:
        log.exception(e)
        self.stop = True
    log.info("{} id={} stopped".format(self.name, self.id))
