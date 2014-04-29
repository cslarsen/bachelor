#!/bin/bash

# This is a build-and-install script I made to deploy faster while working.

echo "------------"
echo "Building ovs"
echo "------------"
echo ""
pushd .
cd ~/ovs
make || exit 0
echo ""
echo "----------"
echo "Installing"
echo "----------"
echo ""
sudo make install
echo ""
sudo make modules_install || exit 0
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
sudo /etc/init.d/openvswitch-controller stop
sudo /etc/init.d/openvswitch-switch restart
sudo /etc/init.d/openvswitch-controller start
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
