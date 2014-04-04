#!/usr/bin/env python

"""
Command-line program that boots a given Mininet.

Must be started in the ~/pox directory on the mininet VM.
(It needs to import both Mininet and POX to work)
"""

import os
import sys

# Add POX and Paxos directories
sys.path.insert(0, "/home/mininet/pox")
sys.path.insert(0, "/home/bach/paxos")

from mininet.cli import CLI
from mininet.util import dumpNodeConnections

from paxos.log import log
from paxos.net import mininet
from paxos.topology import SimpleTopology

def noop(net):
  """A command that does nothing."""
  pass

def ping_listen(net):
  """Starts ping-listeners on all hosts."""
  log.info("Starting ping listeners")

  for node in net.hosts:
    if node.name[0] == "h": # a host?
      cmd = "python ~/bach/paxos/client.py ping-listen &"
      log.info("Launching ping-listener on {}: {}".format(node, cmd))
      node.cmd("python ~/bach/paxos/client.py ping-listen &")

def key_value_server(net):
  """Starts key-value servers on all hosts."""
  log.info("Starting ping listeners")

  for node in net.hosts:
    if node.name[0] == "h": # a host?
      cmd = "python ~/bach/python/key-value-store/server.py &"
      log.info("Launching key-value server on {}: {}".format(node, cmd))
      node.cmd(cmd)

commands = {
  "kv-server": key_value_server,
  "ping-listen": ping_listen,
}

topologies = {"simple": SimpleTopology}

def command_name(cmd):
  """Looks up name of command."""
  if not cmd in commands.values():
    return "?"
  else:
    return [it for it in commands.items() if it[1] == cmd][0][0]

def isroot():
  """Returns True if we're running as root."""
  return os.geteuid() == 0
def boot(topology, command=None):
  if not isroot():
    log.error("Mininet must be run as root.")
    sys.exit(1)

  log.info("Starting Mininet w/topology {} and command {}".
    format(topology.__name__, command_name(command)))

  with mininet(topology()) as net:
    try:
      print("Node connections:")
      dumpNodeConnections(net.hosts)
      log.info("Pinging all")
      net.pingAll()

      if command is not None:
        command(net)

      # Bring up command line interface
      CLI.prompt = "paxos/mininet> "
      CLI(net)

      log.info("Shutting down")
    except KeyboardInterrupt:
      print("")
      log.warn("Interrupted, shutting down")

def print_help():
  print("Usage: boot-mininet.py [topology] [command]")
  print("Known topologies: {}".format(", ".join(topologies.keys())))
  print("Known commands: {}".format(", ".join(commands.keys())))

def parse_args(args):
  """Parse command line arguments, returning topology class and command."""
  topology = None
  command = None

  for arg in args[1:]:
    if arg.startswith("-"):
      if arg == "-h" or arg == "--help":
        print_help()
        sys.exit(0)
      else:
        print("Error: Unknown switch '{}'".format(arg))

    if topology is None:
      if arg in topologies:
        topology = topologies[arg]
        continue
      else:
        print("Error: Unknown topology '{}'".format(arg))
        print("Known topologies: {}".format(", ".join(topologies.keys())))
        sys.exit(1)

    if command is None:
      if arg in commands:
        command = commands[arg]
        continue
      else:
        print("Error: Unknown command '{}'".format(arg))
        print("Known commands: {}".format(", ".join(commands.keys())))
        sys.exit(1)

  if topology is None: topology = SimpleTopology
  if command is None: command = noop

  return topology, command

if __name__ == "__main__":
  boot(*parse_args(sys.argv))
  sys.exit(0)
