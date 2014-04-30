#!/bin/bash

# This is a build-and-install script I made to deploy faster while working.
# If you run it, it will do this:
#
#   - Compile Open vSwitch, exiting on errors.
#   - Install the built software
#   - Reinstall kernel modules
#   - Restart Open vSwitch services, bringing up the new ones.
#
# Made to run on the Mininet GNU/Linux VM.

echo "------------"
echo "Building ovs"
echo "------------"
echo ""
pushd .
cd ~/ovs
make || exit 0
echo ""

echo "-----------------"
echo "Stopping services"
echo "-----------------"
echo ""
sudo /etc/init.d/openvswitch-controller stop
sudo /etc/init.d/openvswitch-switch stop

echo ""
echo "----------"
echo "Installing"
echo "----------"
echo ""
sudo make install
echo ""
sudo make modules_install || exit 0
echo ""

echo "Deploying ovs-controller"
# If tests/test-controller exists, install it as /usr/bin/ovs-controller
test -f tests/test-controller \
  && sudo cp tests/test-controller \
             /usr/bin/ovs-controller
echo ""
popd

echo ""
echo "---------------------------"
echo "Reinstalling kernel modules"
echo "---------------------------"
echo ""
echo "sudo rmmod openvswitch"
sudo rmmod openvswitch
echo "depmod -a"
sudo depmod -a
echo ""

# can i change the order of these?
echo "------------------------------------"
echo "Restarting ovs switch and controller"
echo "------------------------------------"
echo ""
sudo /etc/init.d/openvswitch-switch start
# don't start the controller
#sudo /etc/init.d/openvswitch-controller start
echo ""

# check that it's running
echo "----------------"
echo "Showing versions"
echo "----------------"

echo "sudo ovs-vsctl show"
sudo ovs-vsctl show
echo ""

echo "modinfo openvswitch"
modinfo openvswitch
echo ""
