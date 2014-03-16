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

class paxos:
  @staticmethod
  def marshal(data):
    """Marshal a message going to the Paxos subsystem."""
    return marshal(("PAXOS", data))

  @staticmethod
  def unmarshal(payload):
    command, data = unmarshal(payload)
    assert(command == "PAXOS")
    return data

  @staticmethod
  def isrecognized(payload):
    """Returns True if message contains a client-message."""
    try:
      client.unmarshal(payload)
      return True
    except:
      return False

class client:
  @staticmethod
  def marshal(data):
    """Marshal a message meant to go between the client end-systems."""
    return marshal(("CLIENT", data))

  @staticmethod
  def unmarshal(payload):
    """Unmarshal a message menat to go between the client end-systems."""
    command, data = unmarshal(payload)
    assert(command == "CLIENT")
    return data

  @staticmethod
  def isrecognized(payload):
    """Returns True if message contains a Paxos-message."""
    try:
      paxos.unmarshal(payload)
      return True
    except:
      return False
