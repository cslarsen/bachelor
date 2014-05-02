#!/bin/bash

# Attach gdb to running ovs-vswitchd

PIDFILE=/usr/var/run/openvswitch/ovs-vswitchd.pid

nopid_abort() {
  echo "No PID file $PIDFILE"
  exit 1
}

test -f $PIDFILE || nopid_abort

echo "Attaching gdb to ovs-vswitchd"
PID=`cat $PIDFILE`
echo "gdb -p $PID"
sudo gdb -p $PID
