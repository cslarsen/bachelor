#!/bin/bash

run() {
  echo "-- $* --"
  $*
  echo "--"
  echo ""
}

dumpflows() {
  run sudo ovs-ofctl dump-flows S1
}

# Note, it seems the switch is network-aware, so you can't insert whatever
# address you want here, it needs to be something it knows it can handle
# (probably it looks at the NICs network + netmask)
IP=10.0.0.9
CODE=1
echo "Add flow: Run code $CODE when sending to $IP"
run sudo ovs-ofctl del-flows S1
run sudo ovs-ofctl add-flow S1 idle_timeout=120,ip,nw_dst=$IP,actions=run_code:$CODE
dumpflows
