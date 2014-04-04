HOW TO LAUNCH:

    $ sudo mn --topo single,3 --switch ovsk --controller remote
                                                         ^^^^^^

  then start the Paxos POX controller, verifying that it announces itself in
  the log:

    ./pox.py log.level --DEBUG path.to.paxos

  where path.to.paxos should be a subdirectory from the POX-directory that
  holds this file.

EASIER WAY TO START:

    $ ssh mininet
    $ cd paxos; make pox

    In other window
    $ ssh mininet
    $ cd paxos; sudo python test-client-ctrl.py

    Now try in mininet REPL:
    paxos/mininet> h1 python clients.py 10.0.0.1 1234

    Should detect a client message.

ABOUT:

  This is not full Paxos! It only provides ACCEPT and LEARN messages, and
  this controller is the SOLE LEADER of the Paxos system.

  Aim: Show that by moving Paxos-functionality from the controller down to
  the OpenFlow-tables in the switches, we will achieve a performance gain
  compared to a system where Paxos is implemented in the nodes.

  We must also show that this performance gain would still be valid if we
  implemented the all of Paxos.

TODO:

  - find out how many switches there are
  - need to know how many nodes we have
  - need to route messages as hub/switch
  - need to be able to discern Paxos and client-messages

