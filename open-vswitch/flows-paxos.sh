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
S1=11:11:11:11:11:11
S2=22:22:22:22:22:22
S3=33:33:33:33:33:33
C1=06:e1:1f:f7:f3:2e
H9=de:11:72:88:7e:fd

ofctl() {
  echo "  $*"
  sudo ovs-ofctl $*
}

echo "Clearing all flows"
ofctl del-flows S1
ofctl del-flows S2
ofctl del-flows S3

echo "S1: On client from WAN, send accept to S2 and S3"
ofctl add-flow S1 in_port=$S1_WAN,dl_type=$CLIENT,actions=paxos:onclient,mod_dl_src=$S1,mod_dl_dst=$S2,output:$S1_S2,mod_dl_dst=$S3,output:$S1_S2
echo "S1: On LEARN from S2, send packet to H9"
ofctl add-flow S1 in_port=$S1_S2,dl_type=$LEARN,actions=paxos:onlearn,mod_dl_dst=$H9,output:$S1_S2
echo "S1: Forward packet to H9"
ofctl add-flow S1 dl_dst=$H9,actions=output:$S1_WAN
echo ""

echo "S2: On ACCEPT from S1, send LEARN to S1 and S3"
ofctl add-flow S2 in_port=$S2_S1,dl_type=$ACCEPT,actions=paxos:onaccept,mod_dl_src=$S2,mod_dl_dst=$S1,output:$S2_S2,mod_dl_dst=$S3,output:$S2_S3
echo "S2: On LEARN, send packet to C1"
ofctl add-flow S2 dl_type=$LEARN,actions=paxos:onlearn,mod_dl_dst=$C1,output:$S2_S1
echo "S2: Forward to S1"
ofctl add-flow S2 dl_dst=$S1,actions=output:$S2_S1
echo "S2: Forward to S3"
ofctl add-flow S2 dl_dst=$S3,actions=output:$S2_S3
echo "S2: Forward to H9"
ofctl add-flow S2 dl_dst=$H9,actions=output:$S2_S3
echo "S2: Forward to C1"
ofctl add-flow S2 dl_dst=$C1,actions=output:$S2_S1
echo ""

echo "S3: On ACCEPT from S1, send LEARN to S1 and S2"
ofctl add-flow S3 in_port=$S3_S2,dl_type=$ACCEPT,actions=paxos:onaccept,mod_dl_src=$S3,mod_dl_dst=$S1,output:$S3_S2,mod_dl_dst=$S2,output:$S3_S2
echo "S3: On LEARN, send packet to C1"
ofctl add-flow S3 dl_type=$LEARN,actions=paxos:onlearn,mod_dl_dst=$C1,output:$S3_S2
echo "S3: Forward to H9"
ofctl add-flow S3 dl_dst=$H9,actions=output:$S3_H9
echo "S3: Forward to C1"
ofctl add-flow S3 dl_dst=$C1,actions=output:$S3_S2
echo ""
