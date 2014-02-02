Controlling VirtualBox from Python
==================================

Here is a sample script `start.py` that directly uses the Python
`vboxapi` that comes with VirtualBox.

This API is rather badly documented, but some info can be found at
https://www.virtualbox.org/sdkref/index.html

start.py
--------

This script boots up a VM called "Mininet" and launches some commands on it.
The script is not very stable, though, because the default Mininet VM uses
GRUB _without_ any timeout in the boot sequence. So after powering down the
machine a couple of times you'll get the GRUB "safe-mode" screen which
_requires_ user action to continue. This doesn't work well, especially for
headless (no GUI) mode.

A better alternative _may_  be to use the `pyvbox` module, seen below.

The pyvbox package
------------------

A module that seems to wrap `vboxapi` in a more easy to use manner is
`pyvbox`.  You can either download it directly from the net or just use
`pip`:

    $ sudo pip install pyvbox

You can do a lot of cool stuff here, including capturing PNG screenshots,
videos, execute commands, control the machine, etc.

Here's an example session:

    $ python
    >>> import virtualbox
    >>> vbox = virtualbox.VirtualBox()
    >>> [vm.name for vm in vbox.machines]
    [u'Mininet']
    >>> vm = vbox.find_machine("Mininet")
    >>> eth0 = vm.get_network_adapter(0)
    >>> eth0.mac_address

You can also start a guest session to be able to log on to the machine as an
ordinary user, or you can start a session to control the machine (including
locking it for changes, etc.)

    >>> session = vm.create_session()
    >>> # etc.

The full documentation for pyvbox is available at

    https://pyvbox.readthedocs.org/en/latest/

