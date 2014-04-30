Modified Open vSwitch for thesis project
========================================
While doing my thesis, I had to make some changs to Open vSwitch (ovs). You
can find them in ovs/.  This directory contains its own git repository
cloned form the official Open vSwitch github repo.

Branch
------
I've made a branch off origin/branch-2.1 called "thesis".

To see all the changes I've made,

   $ cd ovs
   $ git log origin/branch-2.1..thesis

Building and deploying
----------------------
I've made a script that will build Open vSwitch and deploy it, if
compilation is successful.

    $ ./deploy-ovs.sh

It will remove existing kernel modules and stop all ovs services, install
the new software and start everything up again.  It will only work on a
Linux machine.  I've used the Mininet VM from their site as a basis.

Author
------
Written by Christian Stigen Larsen in April, 2014.

License
-------
My changes follow the license of the original Open vSwitch project.
