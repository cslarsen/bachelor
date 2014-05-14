#!/usr/bin/env python

"""
Command-line program that boots a given Mininet.

Must be started in the ~/pox directory on the mininet VM.
(It needs to import both Mininet and POX to work)
"""

from signal import SIGINT
import datetime
import os
import sys

# Add POX and Paxos directories
sys.path.insert(0, "/home/mininet/pox")
sys.path.insert(0, "/home/mininet/bach")

# If you want to use the newest mininet version, uncomment the line below.
sys.path.insert(0, "/home/mininet/mininet")

from mininet.cli import CLI
from mininet.net import VERSION
from mininet.util import dumpNodeConnections
#from mininet.util import pmonitor

from paxos.log import log
from paxos.net import mininet
from paxos.topology import SimpleTopology, BaselineTopology, PaxosTopology

class ExitMininet(Exception):
  """Exception used to exit mininet for commands."""
  pass

def noop(net):
  """A command that does nothing."""
  pass

noping = noop

def baseline_benchmark(
    net,
    probe_count=2000,
    probe_interval_secs=0.01,
    src="h1",
    dst="h9",
    output_filename="/home/mininet/pings.txt"):
  """Starts an ICMP PING test, writing results to file."""

  def find_host(name):
    """Find and return host in network or return False."""
    for n in net.hosts:
      if n.name == name:
        return n
    log.critical("Could not find node {} in {}".
        format(name, map(lambda n: n.name, net.hosts)))
    return False

  # Find hosts
  src = find_host(src)
  dst = find_host(dst)

  # Exit if nodes were not found
  if not (src and dst):
    raise ExitMininet()

  for n in src, dst:
    log.info("{} has MAC {} and IP {}".format(n.name, n.MAC(), n.IP()))

  # Note: It's also possible to have a timeout in the loop below,
  # and then p[src].send_signal(SIGINT) when we time out.

  log.info("--- Staring ICMP PING Benchmark ---")

  cmd = ["sudo",
         "ping",
         "-i{}".format(probe_interval_secs),
         "-c{}".format(probe_count),
         dst.IP()]

  log.info("Will overwrite and copy output to {}".format(output_filename))

  # Start process and pipe output to file
  with open(output_filename, "wt") as f:
    try:
         # icmp must cross 4 links at 5 ms latency and back
        expected_rtt_secs = 40/1000

        # The largest value of interval/rtt "shadows" the other
        eta_secs = max(expected_rtt_secs, probe_interval_secs)*probe_count

        log.info("Writing ping output to: %s" % output_filename)
        log.info("The controller will print dots for MAC table misses")

        # Use a dict in case we want to use pmonitor()
        p = {src: src.popen(cmd[0], *cmd[1:], stdout=f)}
        log.info("Started PID {} on {}: {}".format(
          p[src].pid, src.name, " ".join(cmd)))

        # Calc and print ETA
        delta = datetime.timedelta(seconds=int(eta_secs))
        log.info("Estimated test to take %s" % delta)
        eta = datetime.datetime.now() + delta
        log.info("ETA %s" % eta.strftime("%H:%M:%S"))

        log.info("Waiting for pings to finish (output is piped to file for performance)")
        p[src].wait()
        log.info("PID {} finished".format(p[src].pid))
    except KeyboardInterrupt:
      log.warning("Test interrupted")
      log.warning("Sending SIGINT to PID {}".format(p[src].pid))
      p[src].send_signal(SIGINT)
    except Exception:
      log.warning("Test interrupted")
      log.warning("Sending SIGINT to PID {}".format(p[src].pid))
      p[src].send_signal(SIGINT)

  log.info("--- Ending ICMP PING Benchmark ---")
  raise ExitMininet()

def baseline_benchmark_noflows(*args, **kwargs):
  """Runs ICMP PING test with no flow table entries."""
  kwargs["output_filename"] = "/home/mininet/pings-noflows.txt"
  return baseline_benchmark(*args, **kwargs)

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
  "baseline-bench": baseline_benchmark,
  "baseline-bench-noflows": baseline_benchmark_noflows,
  "kv-server": key_value_server,
  "noop": noop,
  "ping-listen": ping_listen,
  "noping": noping,
}

topologies = {"simple": SimpleTopology,
              "baseline-topo": BaselineTopology,
              "paxos-topo": PaxosTopology}

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

  log.info("Mininet version {}".format(VERSION))
  log.info("Starting Mininet w/topology {} and command {}".
    format(topology.__name__, command_name(command)))

  topo = topology()
  with mininet(topo) as (net, ctrl):
    try:
      print("Node connections:")
      dumpNodeConnections(net.hosts)

      # TODO: For some reason, this does not work (conflict of port usage)
      #while not net.controller.checkListening(ctrl):
      #  log.critical("Waiting for the remote controller to start ...")
      #  time.sleep(1)

      # Don't ping all hosts when benchmarking, we want to have a clean slate
      if command not in [baseline_benchmark,
                         baseline_benchmark_noflows,
                         noping]:
        # TODO: Wait until controller is online
        net.pingAll()

      if command is not None:
        command(net)

      if topology == PaxosTopology:
        print("Port WAN1 -> S1: {}".format(topo.port("WAN1", "S1")))
        print("Port S1 -> S2: {}".format(topo.port("S1", "S2")))
        print("Port S2 -> S3: {}".format(topo.port("S2", "S3")))
        print("Port S3 -> h9: {}".format(topo.port("S3", "h9")))
        for node in net.hosts:
          print("{} MAC: {}".format(node.name, node.MAC()))
        #for sw in net.switches:
        #  print("{} controlintf mac {}".format(sw.name, sw.defaultIntf().MAC()))
        #  for no, intf in enumerate(sw.intfList()):
        #    if intf.name.startswith("lo"):
        #      continue
        #    print("{} {} {} MAC {}".format(no, sw.name, intf.name, intf.MAC()))

      # Bring up command line interface
      CLI.prompt = "paxos/mininet> "
      CLI(net)

    except ExitMininet:
      pass
    except KeyboardInterrupt:
      print("")
      log.warn("Interrupted, shutting down")
    finally:
      log.info("Shutting down")

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
