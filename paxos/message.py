"""
Contains functions for marshalling and unmarshalling application level
messages.
"""

import pickle

def marshal(data):
  """General way of marshalling any Python object to a wire-compatible
  format."""
  return pickle.dumps(data, protocol=2)

def unmarshal(data):
  """General way of unmarshalling any Python object from a wire-compatible
  format.  If unmarshalling does not work, this will raise an exception."""
  return pickle.loads(data)

class Message:
  """A way to create and extract application-level messages."""
  def __init__(self, header):
    self.header = header

  def marshal(self, data):
    """Marshal a message, making it wire-ready."""
    return marshal((self.header, data))

  def unmarshal(self, payload):
    """Unmarshal a message, extracting Python objects."""
    command, data = unmarshal(payload)
    assert(command == self.header)
    return data

  def isrecognized(self, payload):
    """Returns True if payload is recognized as a message of this type."""
    try:
      self.unmarshal(payload)
      return True
    except AssertionError:
      return False

class Client(Message):
  """Defines client messages."""
  def __init__(self):
    Message.__init__(self, header="client")

  def ping(self, cookie):
    """Creates a ping message."""
    return self.marshal(("ping", (cookie,)))

  def ping_reply(self, cookie):
    """Creates a ping message."""
    return self.marshal(("ping-reply", (cookie,)))

class Paxos(Message):
  """Defines Paxos messages."""
  def __init__(self):
    Message.__init__(self, header="client")

  def accept(self, crnd, cval):
    """Creates an ACCEPT message."""
    return self.marshal((crnd, cval))

  def learn(self, rnd, vval):
    """Createes a LEARN message."""
    return self.marshal((rnd, vval))

# Instantiate so we can do message.paxos.accept(...) to create a message.
client = Client()
paxos = Paxos()
