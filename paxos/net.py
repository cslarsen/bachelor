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
def mininet(topology, shutdown_controller=True):
  """Builds a Mininet with given topology, returns network and remote
  controller.

  This is a context-sensitive function, so you should use like

      >>> with mininet(SimpleTopology) as (net, ctrl):
            pass
      >>

  which will then shut down both the controller and network automatically.
  """

  net = create_mininet(topology)

  # Doing it this way means we have to manually start our controller on the
  # command line
  C0 = RemoteController("C0", ip="127.0.0.1", port=6633)
  net.addController(C0)

  net.build()
  net.start()

  # Return this immediately to the caller
  yield net, C0

  net.stop()
