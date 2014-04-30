Modified Open vSwitch for thesis project
========================================

While doing my thesis, I had to make some changs to Open vSwitch. You can
find them in ovs/.  This directory contains its own git repository cloned
form the official Open vSwitch github repo.

To see all the changes I've made,

   $ cd ovs
   $ git log 3d0b83890d057d4d1a486139abdcb8b367c15576:HEAD

You'll also find some development notes and a deployment script.
The script will compile ovs and deploy it on the current Linux machine, if
compilation had no errors.  It will stop and remove existing services and
install the new ones.

Author
------
Written by Christian Stigen Larsen in April, 2014.

License
-------
My changes follow the license of the original Open vSwitch project.
