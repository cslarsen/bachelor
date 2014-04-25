from mininet.topo import Topo
from log import log

class SimpleTopology(Topo):
  """A Mininet topology consisting of switches and hosts."""
  def __init__(self,
               count_switches=2,
               hosts_per_switch=3,
               count_clients=1,
               **kw):

    Topo.__init__(self, *kw)

    # Require at least one switch, client and host
    assert(count_switches > 0)
    assert(count_clients > 0)
    assert(hosts_per_switch > 0)

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

    # TODO: For redundancy, add link between each switch as well
    # (e.g. sw0 -> sw1, sw1 -> sw2, sw2->sw0. In the above algorithm, other
    # switches are only connected to the first switch).


class BaselineTopology(Topo):
  """The topology used for baseline."""
  def __init__(self, **kw):
    Topo.__init__(self, *kw)

    log.info("---------------------------")
    log.info("Setting up BaselineTopology")
    log.info("---------------------------\n")

    link_options = {"bw": 10,
                    "delay": "5ms",
                    "loss": 0,
                    "use_htb": True} # Use Hierarchical Token Bucket

    log.debug("Link options: {}".format(link_options))

    # Add client
    c1 = self.addHost("c1")
    log.debug("Adding client {}".format(c1))

    # Add switch S1
    S1 = self.addSwitch("S1")
    log.debug("Adding switch {}".format(S1))
    for n in range(1,4):
      h = self.addHost("h%d" % n)
      log.debug("Adding host {} to switch {}".format(h, S1))
      self.addLink(h, S1, **link_options)

    # Add switch S2
    S2 = self.addSwitch("S2")
    log.debug("Adding switch {}".format(S2))
    for n in range(4,7):
      h = self.addHost("h%d" % n)
      log.debug("Adding host {} to switch {}".format(h, S2))
      self.addLink(h, S2, **link_options)

    # Add switch S3
    S3 = self.addSwitch("S3")
    log.debug("Adding switch {}".format(S3))
    for n in range(7,10):
      h = self.addHost("h%d" % n)
      log.debug("Adding host {} to switch {}".format(h, S3))
      self.addLink(h, S3, **link_options)

    # Connect client to switch
    log.debug("Adding client {} to switch {}".format(c1, S1))
    self.addLink(c1, S1, **link_options)

    # Add links between switches
    log.info("Linking S1 and S2")
    self.addLink(S1, S2, **link_options)
    #
    log.info("Linking S2 and S3")
    self.addLink(S2, S3, **link_options)
