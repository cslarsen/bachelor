from mininet.topo import Topo

class SimpleTopology(Topo):
  """A Mininet topology consisting of switches and hosts."""
  def __init__(self, count_switches=3, hosts_per_switch=3, **kw):
    Topo.__init__(self, *kw)

    # Add switches
    switches = []
    for n in range(0, count_switches):
      switch = self.addSwitch("s%d" % n)
      switches.append(switch)

      # Add hosts to switch
      for m in range(hosts_per_switch):
        host = self.addHost("h%d" % m)
        self.addLink(host, switch, bw=10, delay="5ms", loss=0, use_htb=True)

    # Add links between switches
    for sw in switches[1:]:
      self.addLink(switches[0], sw, bw=10, delay="5ms", loss=0,
          use_htb=True)
