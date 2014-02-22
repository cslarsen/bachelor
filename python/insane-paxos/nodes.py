class Nodes(object):
  """Utility class that keeps track of all nodes in a Paxos system."""
  def __init__(self):
    self.nodes = {}

  def __len__(self):
    return len(self.nodes)

  def __iter__(self):
    return self.nodes.itervalues()

  def __getitem__(self, key):
    ip, port, _ = self.nodes[key]
    return (ip, port)

  def __setitem__(self, key, value):
    self.nodes[key] = value

  @property
  def acceptors(self):
    """Returns all acceptors."""
    return [(ip, port) for (ip, port, kind) in self.nodes.values()
            if kind == "acceptor"]

  @property
  def learners(self):
    """Returns all learners."""
    return [(ip, port) for (ip, port, kind) in self.nodes.values()
            if kind == "learner"]

  @property
  def proposers(self):
    """Returns all proposers."""
    return [(ip, port) for (ip, port, kind) in self.nodes.values()
            if kind == "proposer"]

  def get_id(self, (ip, port)):
    """Look up ID based on address."""

    # Normalize IP-address
    if ip == "127.0.0.1":
      ip = "0.0.0.0"

    for key, (vip, vport, _) in self.nodes.items():
      if (vip, vport) == (ip, port):
        return key

    raise KeyError("No node with address ({}, {})".format(ip, port))
