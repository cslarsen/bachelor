from contextlib import contextmanager

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import CPULimitedHost, RemoteController

def create_mininet(topology):
  return Mininet(topo=topology,
                 host=CPULimitedHost,
                 link=TCLink,
                 build=False)

@contextmanager
def mininet(topology):
  net = create_mininet(topology)

  # Doing it this way means we have to manually start our controller on the
  # command line
  c0 = RemoteController("c0", ip="127.0.0.1", port=6633)
  net.addController(c0)

  net.build()
  net.start()
  yield net
  net.stop()
