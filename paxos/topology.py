from mininet.topo import Topo
from paxos import log

class SimpleTopology(Topo):
  """A Mininet topology consisting of switches and hosts."""
  def __init__(self, count_switches=1, hosts_per_switch=3, **kw):
    Topo.__init__(self, *kw)

    # Add switches
    switches = []
    hostno = 0
    for n in range(0, count_switches):
      switch = self.addSwitch("s%d" % n)
      log.debug("Adding switch {}".format(switch))
      switches.append(switch)

      # Add hosts to switch
      for _ in range(hosts_per_switch):
        host = self.addHost("h%d" % hostno)
        hostno += 1
        log.debug("Adding host {} to switch {}".format(host, switch))
        self.addLink(host, switch, bw=10, delay="5ms", loss=0, use_htb=True)

    # Add links between switches
    for sw in switches[1:]:
      self.addLink(switches[0], sw, bw=10, delay="5ms", loss=0,
          use_htb=True)
