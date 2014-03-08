"""
Contains functions for marshalling and unmarshalling application level
messages.
"""

import pickle

def marshal(data):
  return pickle.dumps(data, protocol=2)

def unmarshal(data):
  return pickle.loads(data)
