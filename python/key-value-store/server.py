"""
Module for very simple key value store in Python,
using UDP.
"""

import pickle

import log
import message
import udp

class Server(object):
  def __init__(self, ip="0.0.0.0", port=1234, db={}):
    self.db = db
    self.ip = ip
    self.port = port

  def put(self, key, value):
    self.db[key] = value

  def get(self, key):
    try:
      return self.db[key]
    except KeyError:
      return None

  def ping(self):
    return message.response("Ping reply")

  def serve(self):
    """Serves messages in a loop."""
    log.info("Serving messages on {}:{}".format(self.ip, self.port))

    for ip, port, data in udp.recv(self.ip, self.port):
      log.debug("FROM {}:{} got '{}'".format(ip, port,
        pickle.loads(data)))
      command, args = message.parse(data)
      response = self.dispatch(command, args, ip, port)
      udp.send(ip, port, message.response(response))

  def dispatch(self, command, args, ip, port):
    if command == "ping":
      log.info("PING from client {}:{}".format(ip, port))
      return "Ping reply"
    elif command == "get":
      key = args
      value = self.get(key)
      log.info("GET from {}:{} key='{}' value='{}'".format(ip, port, key,
        value))
      return value
    elif command == "put":
      key, value = args
      log.info("PUT from {}:{} key='{}' value='{}'".format(ip, port, key,
        value))
      return self.put(key, value)
    else:
      log.error("UNKNOWN command from {}:{} '{}'".format(ip, port,
        command))

if __name__ == "__main__":
  try:
    ip = "0.0.0.0"
    port = 1234
    Server(ip, port).serve()
  except KeyboardInterrupt:
    pass
