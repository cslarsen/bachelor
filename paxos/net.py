from contextlib import contextmanager

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import CPULimitedHost

def create_mininet(topology):
  return Mininet(topo=topology,
                 host=CPULimitedHost,
                 link=TCLink)

@contextmanager
def mininet(topology):
  net = create_mininet(topology)
  net.start()
  yield net
  net.stop()
