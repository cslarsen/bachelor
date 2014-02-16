"""
Construct and parse messages used by the key-value store.
"""

import pickle

def create(command, data=None):
  # TODO: use *data and expand into tuple
  return pickle.dumps((command, data))

def parse(data):
  try:
    return pickle.loads(data)
  except:
    return ("unknown", data)

def parse_response(data):
  _, reply = parse(data)
  return reply

def put(key, value):
  """Creates a PUT message."""
  return create("put", (key, value))

def get(key):
  """Creates a GET message."""
  return create("get", key)

def ping():
  """Creates a PING message."""
  return create("ping")

def response(data):
  """Creates a RESPONSE message."""
  return create("response", data)
