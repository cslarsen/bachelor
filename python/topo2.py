"""
Starts mininet with the topology defined in topologies/topo2.dot

You can run this file by doing (on the mininet vm):

    $ sudo python topo2.py

Currently, it just creates a network, dumps all nodes and then pings all of them.

NOTE: If you get an error message saying that you must close down something
that is listening, it's probably just a lingering process from an earlier run.
Mininet then conveniently lists all listening sockets along with their PIDs (on
the right side).  Then you just kill the offending procs.
"""

import sys
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

def banner(message, separator="-", where=sys.stdout):
  """Prints the message with separators above and below the message."""
  where.write("\n\n")
  where.write("-" * len(message) + "\n")
  where.write("%s\n" % message)
  where.write("-" * len(message) + "\n")
  where.write("\n")
  where.flush()

class Topo2(Topo):
  """Three switches, one master, three hosts each."""
  def __init__(self, **kw):
    Topo.__init__(self, *kw)

    # Add switches
    switch1 = self.addSwitch("s1")
    switch2 = self.addSwitch("s2")
    switch3 = self.addSwitch("s3")

    # Add hosts
    h1 = self.addHost("h1")
    h2 = self.addHost("h2")
    h3 = self.addHost("h3")
    h4 = self.addHost("h4")
    h5 = self.addHost("h5")
    h6 = self.addHost("h6")
    h7 = self.addHost("h7")
    h8 = self.addHost("h8")
    h9 = self.addHost("h9")

    # Add links between switches; switch1 is the master
    # TODO: Why doesn't this work when we add "use_htb=True" here?
    self.addLink(switch1, switch2, bw=10, delay="5ms", loss=0)
    self.addLink(switch1, switch3, bw=10, delay="5ms", loss=0)

    # Add links between switches and their hosts

    # {h1, h2, h3} -> switch1
    self.addLink(h1, switch1, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h2, switch1, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h3, switch1, bw=10, delay="5ms", loss=0, use_htb=True)

    # {h4, h5, h6} -> switch2
    self.addLink(h4, switch2, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h5, switch2, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h6, switch2, bw=10, delay="5ms", loss=0, use_htb=True)

    # {h7, h8, h9} -> switch3
    self.addLink(h7, switch3, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h8, switch3, bw=10, delay="5ms", loss=0, use_htb=True)
    self.addLink(h9, switch3, bw=10, delay="5ms", loss=0, use_htb=True)

def main():
  """Create network and bring up CLI."""

  print("Initializing network")
  topo = Topo2()
  net = Mininet(topo=topo,
                host=CPULimitedHost, link=TCLink)

  # Don't trap CTRL+C until network has been started
  print("Starting up network")
  net.start()
    
  try:
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    
    print("Testing network connectivity")
    net.pingAll()
    
    print("Stopping")
    net.stop()
  except KeyboardInterrupt:
    banner("CTRL+C, please wait for network to stop.", where=sys.stderr)
    net.stop()

if __name__ == "__main__":
  setLogLevel("info")
  main()
