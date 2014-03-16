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

paxos = Message(header="paxos")
client = Message(header="client")
