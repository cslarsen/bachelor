#!/bin/bash

# Script to initialize Open vSwitch after downloading a new version or
# changing branches (basically, if you haven't compiled with the version
# yet, you need to run this script)

pushd .
cd ~/ovs
echo "# boot.sh"
./boot.sh || exit 1
echo "# ./configure --prefix=/usr --with-linux=/lib/modules/`uname -r`/build"
./configure --prefix=/usr --with-linux=/lib/modules/`uname -r`/build || exit 1
popd

echo ""
echo "You can now build and deploy the code with deploy-ovs.sh"
echo ""
