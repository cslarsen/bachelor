"""
Construct and parse messages used by the key-value store.
"""

import pickle

# All messages start with this header
HEADER = "client"

# Command headers
GET = "get"
PING = "ping"
PUT = "put"
RESPONSE = "response"
UNKNOWN = "unknown"

def create(command, data=None):
  """Creates a message for the key-value system."""
  return pickle.dumps((HEADER, (command, data)))

def parse(data):
  """Returns (command, raw-data) from a create() message."""
  try:
    message = pickle.loads(data)
    assert message[0] == HEADER
    return pickle.loads(data)[1]
  except:
    return (UNKNOWN, data)

def parse_response(data):
  """Extracts the data part of a response."""
  command, reply = parse(data)
  assert command == RESPONSE
  return reply

def put(key, value):
  """Creates a PUT message."""
  return create(PUT, (key, value))

def get(key):
  """Creates a GET message."""
  return create(GET, (key,))

def ping():
  """Creates a PING message."""
  return create(PING, tuple())

def response(data):
  """Creates a RESPONSE message."""
  return create(RESPONSE, data)
