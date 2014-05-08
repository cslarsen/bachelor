#!/bin/bash

IF=`ifconfig | grep eth0 | cut -f1 -d' '`
HOST=10.0.0.11
PORT=1234
SLEEP=0.01

stop() {
  exit 0
}

trap stop SIGINT

while [ true ] ; do
  echo $IF `date` | ./send-udp -r -w5 $HOST $PORT
  #sleep $SLEEP
done
