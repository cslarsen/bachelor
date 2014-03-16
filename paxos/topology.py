from mininet.topo import Topo
from paxos.log import log

class SimpleTopology(Topo):
  """A Mininet topology consisting of switches and hosts."""
  def __init__(self,
               count_switches=1,
               hosts_per_switch=3,
               count_clients=1,
               **kw):

    Topo.__init__(self, *kw)

    link_options = {"bw": 10,
                    "delay": "5ms",
                    "loss": 0,
                    "use_htb": True}

    # Add client(s) first so their addresses start at 10.0.0.1 and so on.
    clients = []
    for n in range(count_clients):
      client = self.addHost("cl%d" % n)
      log.debug("Adding client {}".format(client))
      clients.append(client)

    # Add switches
    switches = []
    hostno = 0
    for n in range(count_switches):
      switch = self.addSwitch("s%d" % n)
      log.debug("Adding switch {}".format(switch))
      switches.append(switch)

      # Add hosts to switch
      for _ in range(hosts_per_switch):
        host = self.addHost("h%d" % hostno)
        hostno += 1
        log.debug("Adding host {} to switch {}".format(host, switch))
        self.addLink(host, switch, **link_options)

    # Connect client(s) to first switch
    cl0 = clients[0]
    s0 = switches[0]
    log.debug("Adding client {} to switch {}".format(cl0, s0))
    self.addLink(cl0, s0, **link_options)

    # Add links between switches
    for sw in switches[1:]:
      self.addLink(switches[0], sw, **link_options)
