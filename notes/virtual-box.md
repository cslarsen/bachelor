How to set up VirtualBox
------------------------

Mininet VM
----------
You need the Mininet VM (2.1.0). You have to create a new VM in VirtualBox
and point the HD to the mininet image.

Network setup
-------------
In VirtualBox, go to preferences, network, host-only networks and add a
network. Just click OK.

In the VM, set up host-only network. This allows communication between the
host and the virtual machine only.

You should also set up a NAT network on the VM so that it can reach the
internet.

You can now ssh into the VM by using the host network IP-address 192.*.  The
host computer should be reachable on 192.*.*.1, so you can, for instance,
run the OpenFlow controller on the host machine if you wish.

SSH
---
You should use the host-only network to SSH in to the VM.
This means it will have an 192.* IP-address that you can rely on (it will
not change if you move your host computer on another network).

SSH config
----------

I have the following entry for mininet in my `~/.ssh/config`:


    Host mininet
    User mininet
    Hostname 192.168.56.101
    ForwardX11 yes

I've also copied my public ssh key `~/.ssh/id_rsa.pub` into the VM at
`./ssh/authorized_keys` so that I can now just type `ssh mininet` to log on the
the VM.

X11 is also forwarded, so you should be able to bring up an xterm by doing

    $ ssh mininet xterm &

On Mac OS X you need XQuartz for this to work.
