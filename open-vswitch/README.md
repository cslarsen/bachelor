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
I've made some helper scripts for compiling and deploying Open vSwitch.
Whenever you switch branches, you should clean out all files. Instead of
running `make clean` it's faster to let git clean up for you. Then you must
run boot.sh and configure through the init-ovs.sh script:

    $ cd ovs/
    $ git clean -fdx
    $ ~/init-ovs.sh

You can now build and deploy ovs:

    $ ./deploy-ovs.sh

It will compile ovs (halting on errors), install the targets, redeploy
kernel modules and software and restart all services.

As said, it will only work on a Linux box. I've used these scripts on the
Mininet Linux VM from their site as a basis.

Author
------
Written by Christian Stigen Larsen in April, 2014.

License
-------
My changes follow the license of the original Open vSwitch project.
