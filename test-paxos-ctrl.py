"""
Test program for the Paxos POX controller.
"""

import os
import sys

from mininet.cli import CLI
from mininet.util import dumpNodeConnections

from paxos.log import log
from paxos.net import mininet
from paxos.switches import SimpleTopology

def isroot():
  return os.geteuid() == 0

if not isroot():
  log.error("Must be run as root")
  sys.exit()

log.info("Starting mininet")

with mininet(SimpleTopology()) as net:
  print("Node connections:")
  dumpNodeConnections(net.hosts)
  log.info("Pinging all")
  net.pingAll()

  # Bring up command line interface
  CLI.prompt = "paxos/mininet> "
  CLI(net)

  log.info("Shutting down")
