#!/bin/bash

# Installs flows for Paxos on-switch handling.
#
# You need to restart ovs each time, start up Mininet, get the correct port
# numbers and ether addresses for c1 and h9, then run this script.

# Message typees
CLIENT=0x7a40
ACCEPT=0x7a01
LEARN=0x7a02

# Ports
S1_WAN=3
S1_S2=5
S2_S1=1
S2_S3=5
S3_S2=2
S3_H9=1

# MAC addrs
S1=6e:22:2a:74:02:47
S2=26:5d:7b:b1:fd:44
S3=02:34:38:8e:0d:49
C1=06:e1:1f:f7:f3:2e
H9=de:11:72:88:7e:fd
BC=ff:ff:ff:ff:ff:ff

ofctl() {
  echo "  $*"
  sudo ovs-ofctl $*
}

echo "Clearing all flows"
ofctl del-flows S1
ofctl del-flows S2
ofctl del-flows S3

echo "S1: On client from WAN, send accept to S2 and S3"
ofctl add-flow S1 in_port=$S1_WAN,dl_type=$CLIENT,actions=paxos:onclient,mod_dl_src=$S1,mod_dl_dst=$S3,output:$S1_S2,mod_dl_dst=$S2,output:$S1_S2

echo "S2: On accept, send learns to S1 and S3"
ofctl add-flow S2 dl_dst=$S2,dl_type=$ACCEPT,actions=paxos:onaccept,mod_dl_src=$S2,mod_dl_dst=$S1,output:$S2_S1,mod_dl_dst=$S3,output:$S2_S3

echo ""
echo "FLOWS S1"
sudo ovs-ofctl dump-flows S1
echo ""
echo "FLOWS S2"
sudo ovs-ofctl dump-flows S2
echo ""
echo "FLOWS S3"
sudo ovs-ofctl dump-flows S3
