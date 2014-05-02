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

echo "Flows before adding anything"
dumpflows

echo "Adding two flows (one run_code)"

# add two flows so we can see that the last one (output) is not drop
run sudo ovs-ofctl add-flow S1 priority=1000,dl_type=0x0801,actions=run_code:111 || exit 1
run sudo ovs-ofctl add-flow S1 priority=1000,dl_type=0x0802,actions=output:222 || exit 1

echo "Flows after adding something"
dumpflows
