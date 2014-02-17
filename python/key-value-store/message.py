"""
Construct and parse messages used by the key-value store.
"""

import pickle

def create(command, data=None):
  """Creates a message for the key-value system."""
  return pickle.dumps((command, data))

def parse(data):
  """Returns (command, raw-data) from a create() message."""
  try:
    return pickle.loads(data)
  except:
    return ("unknown", data)

def parse_response(data):
  """Extracts the data part of a response."""
  command, reply = parse(data)
  assert command == "response"
  return reply

def put(key, value):
  """Creates a PUT message."""
  return create("put", (key, value))

def get(key):
  """Creates a GET message."""
  return create("get", (key,))

def ping():
  """Creates a PING message."""
  return create("ping", tuple())

def response(data):
  """Creates a RESPONSE message."""
  return create("response", data)
