"""
Test program for the Paxos POX controller.
"""

import os
import sys

# Add pox to the include path, this assumes you are running this script from
# the pox subdirectory on the mininet instance.
sys.path.insert(0, ".")

from mininet.cli import CLI
from mininet.util import dumpNodeConnections

from paxos.log import log
from paxos.net import mininet
from paxos.topology import SimpleTopology

def isroot():
  return os.geteuid() == 0

def main(start_servers=None):
  if not isroot():
    log.error("Must be run as root")
    sys.exit()

  log.info("Starting mininet")

  with mininet(SimpleTopology()) as net:
    try:
      print("Node connections:")
      dumpNodeConnections(net.hosts)
      log.info("Pinging all")
      net.pingAll()

      if start_servers is not None:
        log.info("Starting ping listeners ...")
        for node in net.hosts:
          if node.name[0] == "h": # a host?
            log.info("Launching ping-listener on {}".format(node))
            node.cmd("python ~/bach/paxos/clients.py ping-listen &")

      # Bring up command line interface
      CLI.prompt = "paxos/mininet> "
      CLI(net)

      log.info("Shutting down")
    except KeyboardInterrupt:
      print("")
      log.warn("Interrupted, shutting down")

if __name__ == "__main__":
  main(*sys.argv[1:])
