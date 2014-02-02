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

  * Open VirtualBox preferences
  * Under network, add a host-network and a nat-network. Note tha
    IP-addresses being used.  On my machine, they are 192.168.56.* and
    10.0.2.* by default.
  * Create a new VM, point to the Mininet image (you can't import it
    directly)
  * Go to network preferences.  For adapter 1, use a host-only network,
    choosing the network you made in the above step.  On adapter 2 choose a
    NAT Network and choose the NAT network made above.
  * Start the VM.  You can log in with the user and password
    mininet/mininet.

The idea is to use the host network for SSH and the SDN.  You could also run
the controller on the host machine if you wanted to.

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

