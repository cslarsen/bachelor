import pickle
import sys
import time

from communication import UDP

class PingClient():
  def __init__(self):
    pass

  def ping(self, to, cookie):
    """Sends a ping message."""
    udp = UDP()
    return udp.sendto(to, pickle.dumps(("PING-MESSAGE", "PING", cookie)))

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print("Usage: ping-client ip port")
    sys.exit(1)

  ip = sys.argv[1]
  port = int(sys.argv[2])
  client = PingClient()
  for i in range(3):
    print("Send ping w/bytes: {}".format(client.ping((ip, port), "Hello, world!")))
    if i<2: time.sleep(1)
