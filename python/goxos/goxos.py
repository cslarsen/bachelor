#!/usr/bin/env python

"""
Starts mininet with the one switch and four hosts, goxos/kvs running on
three of them and a kvsc in benchmark mode on the last.

You need to run this script as root to be able to run.
"""

# TODO: After sendCmd, one can use monitor() to catch output.

import argparse
import json
import os
import sys
import time

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

def argparser():
  p = argparse.ArgumentParser(description="Goxos on Mininet")
  p.add_argument("--delay", type=int, default=0, help="Link delay in ms")
  p.add_argument("--server-config", type=str,
                 default="$PWD/server-config.json",
                 help="Path for Goxos server (kvs) config file")
  p.add_argument("--hosts", type=int, default=4,
                 help="Number of Goxos hosts to start")
  p.add_argument("--bandwidth", type=int, default=10,
                 help="Link bandwidth in megabits per second")
  p.add_argument("--loss", type=int, default=0,
                 help="Link loss integer value, default 0")
  p.add_argument("--kvs", type=str,
                 default="$GOPATH/src/goxosapps/kvs/kvs",
                 help="Path to kvs executable")
  p.add_argument("--kvsc", type=str,
                 default="$GOPATH/src/goxosapps/kvsc/kvsc",
                 help="Path to kvsc executable")
  p.add_argument("--port-paxos", type=int, default=8080,
                 help="Paxos port number")
  p.add_argument("--port-client", type=int, default=8081,
                 help="Client port number")
  p.add_argument("--log", type=str, default="$PWD/logs",
                 help="Path to directory for writing log files")
  p.add_argument("--no-autoconf", default=False, action="store_true",
                 help="Disable automatic creation of config files")
  return p

def log(message):
  sys.stdout.write("%s\n" % message)
  sys.stdout.flush()

def expand_path(path):
  """Expands user variables and user home (~/tilde) in path."""
  return os.path.expandvars(os.path.expanduser(path))

class GoxosTopo(Topo):
  """Sets up a topology consisting of one switch, n-1 goxos servers and 1
  goxos client that will run benchmarks.

  Args:
    num_hosts: Number of hosts to create. One will be a goxos benchmarking
               client, the others will be goxos servers.
    delay_ms: Timeout in milliseconds. Zero is allowed. Because of how
              Goxos is setup, you shouldn't have too high delay. 5ms,
              for instance, is too much and will just hang the system.
    loss: The amount of loss in the network. See mininet.net.topo.addLink
          for documentation.
    use_htb: See mininet.net.topo for documentation.
  """
  def __init__(self,
               num_hosts=4,
               bandwidth_mbit=10,
               delay_ms=0,
               loss=0,
               use_htb=True,
               **kw):
    Topo.__init__(self, **kw)

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
                   delay="%dms" % delay_ms,
                   loss=loss)

class GoxosMininet(Mininet):
  """A Mininet instance with special methods for starting up Goxos servers
  and a client.

  Args:
    kvs: Path to kvs executable, can use $GOPATH and $PWD, etc.
    kvsc: Path to kvsc executable
    port_paxos: Port for servers to communicate on
    port_client: Port for clients to connect to
    log_path: Path to put log files
    config_server: Path to Goxos config file for servers
    config_client: Path to Goxos config file for clients
    create_config: If True, will create config files at the specified
                   locations for the current Goxos setup. This is the
                   default behvaiour. If False, will only attempt to read
                   config files. Note that if set to True, it will
                   OVERWRITE any existing files.
  """
  def __init__(self, 
               kvs="$GOPATH/src/goxosapps/kvs/kvs",
               kvsc="$GOPATH/src/goxosapps/kvsc/kvsc",
               port_paxos=8080,
               port_client=8081,
               config_server="$PWD/server-config.json",
               config_client="$PWD/config.json",
               log_path="$PWD/logs/",
               create_config=True,
               **kw):

    Mininet.__init__(self, **kw)

    self.kvs = expand_path(kvs)
    self.kvsc = expand_path(kvsc)
    self.log = expand_path(log_path)
    self.config_server = expand_path(config_server)
    self.config_client = expand_path(config_client)
    self.create_config = create_config
    self.port_paxos = port_paxos
    self.port_client = port_client

    paths = [self.kvs, self.kvsc, self.log]

    if not self.create_config:
      paths.append(self.config_server)
      paths.append(self.config_client)

    for path in paths:
      if not os.path.exists(path):
        exit("Could not find path: {}".format(path))

  @property
  def client(self):
    """Returns the Goxos client host."""
    return self.hosts[-1]

  @property
  def servers(self):
    """Returns the Goxos servers as (id, Host)."""
    return enumerate(self.hosts[:-1])

  def start_servers(self):
    """Starts up the Goxos servers asynchronously (kvs)."""
    for host_id, host in self.servers:
      cmd = [self.kvs,
             "-v=2",
             "-log_dir=%s" % self.log,
             "-id=%d" % host_id,
             "-config-file=%s" % self.config_server]
      log("{} {}: Starting kvs: {}".format(host, host.IP(), " ".join(cmd)))

      # Start asynchronously
      host.sendCmd(" ".join(cmd))

  def start_client(self):
    """Starts up the Goxos benchmark client synchronously (kvsc)."""
    cmd = "%s -mode=bench" % self.kvsc
    log("{} {}: Starting kvsc: {}".
      format(self.client, self.client.IP(), cmd))
    self.client.cmdPrint(cmd)

  def write_server_config(self,
                          paxos_type="MultiPaxos",
                          failure_handling_type="None"):
    """Writes client config to the given file, for use with kvsc."""

    nodes = {}
    for host_id, host in self.servers:
      nodes[str(host_id)] = {"Ip": host.IP(),
                             "PaxosPort": str(self.port_paxos),
                             "ClientPort": str(self.port_client)}

    config = {"Nodes": nodes,
              "PaxosType": paxos_type,
              "FailureHandlingType": failure_handling_type}

    with open(self.config_server, "wt") as f:
      f.write(json.dumps(config))

  def write_client_config(self):
    nodes = []
    for _, node in self.servers:
      nodes.append("%s:%d" % (node.IP(), self.port_client))

    with open(self.config_client, "wt") as f:
      f.write(json.dumps({"Nodes": nodes}))

def main(args):
  """Create network and bring up CLI."""

  log("Initializing network")
  topo = GoxosTopo(num_hosts=args.hosts,
                   bandwidth_mbit=args.bandwidth,
                   delay_ms=args.delay,
                   loss=args.loss,
                   use_htb=True)

  net = GoxosMininet(topo=topo,
                     host=CPULimitedHost,
                     link=TCLink,
                     kvs=args.kvs,
                     kvsc=args.kvsc,
                     port_paxos=args.port_paxos,
                     port_client=args.port_client,
                     log_path=args.log,
                     create_config=not args.no_autoconf)

  # Don't trap CTRL+C until network has been started
  log("Starting up network")
  net.start()

  try:
    log("Dumping host connections")
    dumpNodeConnections(net.hosts)

    log("Testing network connectivity")
    net.pingAll()

    if net.create_config:
      log("Writing %s" % net.config_server)
      net.write_server_config()
      log("Writing %s" % net.config_client)
      net.write_client_config()

    log("Starting servers")
    net.start_servers()

    wait = 2
    log("Wait %d secs to start client\n" % wait)
    time.sleep(wait)
    net.start_client()

    log("Entering command line interface")
    CLI.prompt = "goxos/mininet> "
    CLI(net)

    log("Stopping")
    net.stop()
  except KeyboardInterrupt:
    log("CTRL+C, please wait for network to stop.")
    net.stop()

if __name__ == "__main__":
  if not "GOPATH" in os.environ:
    exit("No GOPATH environment variable for user id %d\n\n" +
         "If you're using sudo and have GOPATH set locally,\n" +
         "you can run with `sudo -E ./goxos.py` to transfer\n" +
         "the environment over to sudo.\n")
  setLogLevel("info")
  main(argparser().parse_args())
