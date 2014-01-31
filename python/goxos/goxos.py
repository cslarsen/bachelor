"""
Starts mininet with the one switch and four hosts, goxos/kvs running on
three of them and a kvsc in benchmark mode on the last.

You need to run this script as root to be able to run.
"""

import os
import sys

from mininet.cli import CLI
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

class GoxosTopo(Topo):
  """Sets up a topology consisting of one switch, n-1 goxos servers and 1
  goxos client that will run benchmarks.

  Args:
    num_hosts: Number of hosts to create. One will be a goxos benchmarking
               client, the others will be goxos servers.
    timeout_ms: Timeout in milliseconds. Zero is allowed. Because of how
                 Goxos is setup, you shouldn't have too high timeout. 5ms,
                 for instance, is too much and will just hang the system.
    loss: The amount of loss in the network. See mininet.net.topo.addLink
          for documentation.
    use_htb: See mininet.net.topo for documentation.
  """
  def __init__(self,
               num_hosts=4,
               bandwidth_mbit=10,
               timeout_ms=1,
               loss=0,
               use_htb=True,
               **kw):
    Topo.__init__(self, *kw)

    # Add switch
    switch = self.addSwitch("s1")

    # Add hosts
    hosts = []
    for n in range(num_hosts):
      host = self.addHost("h%d" % n)
      hosts.append(host)

      # Link host to switch
      self.addLink(host,
                   switch,
                   bw=bandwidth_mbit,
                   delay=timeout_ms,
                   loss=loss,
                   use_htb=use_htb)

  # TODO: If config_file is None, dynamically create one based on the
  #       current IP addresses for our hosts, etc.
  def start_servers(self,
                    config_file="server-config.json",
                    log_dir="$PWD/logs/",
                    kvs_path="$GOPATH/src/goxosapps/kvs/kvs"):
    """Starts up the Goxos servers (kvs)."""
    for host_id, host in enumerate(self.hosts[:-1]):
      cmd = [kvs_path,
             "-v=2",
             "-log_dir=%s" % os.path.expandvars(log_dir),
             "-id=%d" % host_id,
             "-config-file=%s" % config_file]
      print("{}: Starting kvs: {}".format(host, " ".join(cmd)))

      # Start asynchronously
      pid = host.sendCmd(" ".join(cmd))
      print("{}: kvs pid is {}".format(host_id, pid))

  # TODO: If config_file is None, dynamically create one based on the
  #       current IP addresses for our hosts, etc.
  def start_client(self,
                   config_file="client-config.json",
                   kvsc_path="$GOPATH/src/goxosapps/kvsc/kvsc"):
    """Starts up the Goxos benchmark client (kvsc)."""
    host = self.hosts[-1]
    cmd = [kvsc_path, '-mode="bench"']
    print("{}: Starting kvsc: {}".format(host, " ".join(cmd)))

    # Start synchronously with print
    host.cmdPrint(" ".join(cmd))

def main():
  """Create network and bring up CLI."""

  print("Initializing network")
  topo = GoxosTopo()
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

    net.start_servers()
    CLI(net)

    print("Stopping")
    net.stop()
  except KeyboardInterrupt:
    banner("CTRL+C, please wait for network to stop.", where=sys.stderr)
    net.stop()

if __name__ == "__main__":
  setLogLevel("info")
  main()
