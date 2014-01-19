Current goals
-------------

- Finish the openflow tutorial

- Create some openflow controllers using NOX/POX, Beacon, OpenVSwitch etc.

- Broadcast TCP packages with increasing sequence numbers from one host to
  several hosts on the virtual network.

- Same as above, but try to send the packets from OUTSIDE of the virtual
  network, have the packets be internally broadcasted.

- Using the topology topo2.py, create an easily runnable program that sets this
  up and starts sending TCP packets w/increasing sequence numbers from
  incoming, have this be broadcasted to all the hosts h1.1, ..., h3.3.
  Be able to see the sequence numbers coming in to the hosts, preferrabl in
  ONE place.

- Make it possible to interfer with one of the switches, e.g. have switch2
  fail randoml from time to time or introduce a delay in it (2 seconds,
  e.g.) and see that one of the hosts skips some sequences.

- Implement Paxos on the controller, ensure that the hosts will now receive
  the messages in the correct order, even if one switch fails from time to
  time.

- Using Paxos above, bring down switch1 and see if the network can select a
  new master. See what happens when we pring switch1 back up.

- Move as much stuff from the controller down to the switches. See if this
  is possible and if we have reduced bandwidth between the controller and
  the switches.

Finished goals
--------------

- Set up mininet and send a TCP package with sequence numbers between two
  hosts on mininet (DONE: See counter/notes)

- Create a more advanced network topology like in topologies/topo2.dot
  (topo2.py)
