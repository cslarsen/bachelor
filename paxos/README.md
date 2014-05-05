Installing
----------

Install the Mininet VM, then update the code

    cd ~/mininet; git pull
    cd ~/pox; git pull; git checkout dart # dart = most recent version
    ln -s ~/bach/paxos/ ~/pox/ext

How to launch
-------------

First launch the controller on the mininet vm:

    cd ~/pox; ./pox.py log.level --DEBUG paxos.controller

then launch mininet:

    sudo ~/bach/paxos/boot-mininet.py simple kv-server

Then you can do

    paxos/mininet> cl0 python ~/bach/paxos/client.py kv-client

and make sure that it works.
