from paxos.log import log
from paxos.net import mininet
from paxos.switches import SimpleTopology

log.info("Starting mininet")

with mininet(SimpleTopology()):
  log.info("Started mininet")
  log.info("Shutting down")
