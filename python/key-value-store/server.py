"""
Module for very simple key value store in Python,
using UDP.
"""

import pickle

from dispatch import Dispatcher
import log
import message
import udp

class Server(Dispatcher):
  """A key-value server that responds to certain commands."""
  def __init__(self, ip="0.0.0.0", port=1234, db={}):
    Dispatcher.__init__(self, {
      "get": self.get,
      "ping": self.ping,
      "put": self.put,
    }, self.unknown)

    self.db = db
    self.ip = ip
    self.port = port
    self.udp = udp.UDP(bind_ip=self.ip, bind_port=self.port)

  def put(self, key, value):
    """Stores key with given value in database."""
    self.db[key] = value

  def get(self, key):
    """Retrieves given key from the database."""
    try:
      return self.db[key]
    except KeyError:
      return None

  def ping(self):
    """Reply to ping requests."""
    return "Ping reply"

  def unknown(self, *args):
    command, ip, port = args
    log.error("UNKNOWN command from {}:{} '{}'".format(ip, port, command))

  def serve(self):
    """Serves messages in a loop."""
    log.info("Serving messages on {}:{}".format(self.ip, self.port))

    for data, (ip, port) in self.udp.recv_loop():
      try:
        log.debug("From {}:{} '{}'".format(ip, port, pickle.loads(data)))

        command, args = message.parse(data)
        result = self.dispatch(command, *args)
        self.udp.sendto(ip, port, message.response(result))

        log.info("{}:{} {}({}){}".format(ip, port,
          self.lookup(command).__name__,
          ", ".join(map(str, args)),
          " -> %s" % str(result) if result is not None else ""))
      except Exception, e:
        log.error(e)
        raise
      except KeyboardInterrupt:
        raise

if __name__ == "__main__":
  try:
    Server("0.0.0.0", 1234).serve()
  except KeyboardInterrupt:
    pass
