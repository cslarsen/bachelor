How to set up VirtualBox
------------------------

Prerequisites
-------------

You need

  * The Mininet 2.1.0 VM
  * VirtualBox
  * A X11 server, e.g. XQuartz on Mac OS X

Setting up Mininet VM in VirtualBox
-----------------------------------

Perform the steps from here:

  https://forums.virtualbox.org/viewtopic.php?f=3&t=36574

In other words, in VirtualBox preferences, under Network, add two networks:
NAT and HOST.

You should now login to mininet using ssh on the host-only network, while
the VM can reach the internet using NAT.

It also means that the you can reach the VM on the same host-only IP-address
even if you move the host machine to another network.  You can also probably
run the OpenFlow controller on the host machine.

NAT is only used when the VM needs to reach the internet.

SSH setup
---------

You can now log in to the VM using ssh.  First you need to find out what the
IP-address is.  This can be done by logging into the Mininet VM console and
running `ifconfig` and noticing the 192.* IP-address on eth0.

On my machine this is 192.168.56.101:

    $ ssh mininet@192.168.56.101

Since this is tedious, you should copy your public SSH key to the VM:

    $ ssh ~/.ssh/id_rsa.pub mininet@192.168.56.101 \
      "cat - >> ~/.authorized_keys && chmod go-xrw ~/.ssh/authorized_keys"

Also add the following lines to your `~/.ssh/config` file:

    Host mininet
    User mininet
    Hostname 192.168.56.101
    ForwardX11 yes

You should now be able to start a remote xterm by doing

    $ ssh mininet xterm

