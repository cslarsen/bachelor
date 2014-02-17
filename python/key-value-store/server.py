"""
Module for very simple key value store in Python,
using UDP.
"""

import pickle

from dispatch import Dispatcher
import log
import message
import udp

class Server(object):
  """A key-value server that responds to certain commands."""
  def __init__(self, ip, port, dispatch_table, default_dispatch):
    self.dispatcher = Dispatcher(dispatch_table, default_dispatch)
    self.udp = udp.UDP(bind_ip=ip, bind_port=port)

  def serve(self):
    """Serve messages in a loop."""
    log.info("Listening on {}:{}".format(self.udp.bind_ip,
                                         self.udp.bind_port))

    for data, (ip, port) in self.udp.recv_loop():
      try:
        log.debug("From {}:{} '{}'".format(ip, port, pickle.loads(data)))

        command, args = message.parse(data)
        result = self.dispatcher.dispatch(command, *args)
        self.udp.sendto(ip, port, message.response(result))

        log.info("{}:{} {}({}){}".format(ip, port,
          self.dispatcher.lookup(command).__name__,
          ", ".join(map(str, args)),
          " -> %s" % str(result) if result is not None else ""))
      except Exception, e:
        log.error(e)
        raise
      except KeyboardInterrupt:
        raise

class KeyValueServer(Server):
  def __init__(self, ip, port, initial_db={}):
    Server.__init__(self, ip, port, {
      "get": self.get,
      "ping": self.ping,
      "put": self.put,
    }, self.unknown)

    self.db = initial_db

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
    return "Invalid command"

if __name__ == "__main__":
  try:
    KeyValueServer("0.0.0.0", 1234).serve()
  except KeyboardInterrupt:
    pass
