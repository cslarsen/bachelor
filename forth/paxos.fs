\ Number of Paxos nodes
3 constant |N|
1 constant node.id

: mac.s1 s" 00:00:00:01" ;
: mac.s2 s" 00:00:00:02" ;
: mac.s3 s" 00:00:00:03" ;

\ Persistent variables
variable crnd
variable id
variable vval

\ Utility functions

: dup2 ( a b -- a b a b )
    over over ;

: begin.main ( -- )
  ." ** Constants" cr
  ."    |N| " |N| . cr
  ."    node.id " node.id . cr
  ."    mac.s1 " mac.s1 type cr
  ."    mac.s2 " mac.s2 type cr
  ."    mac.s3 " mac.s3 type cr
  cr

  ." ** Loading values from data table (TODO)" cr

  \ Initialize values
  node.id crnd !
  0 vval !

  ."    crnd " crnd @ . cr
  ."    vval " vval @ . cr
  cr 
  ." --- begin ---" cr ;

: end.main ( -- )
  ." --- end ---" cr
  cr
  ." ** Saving values from data table (TODO)" cr
  ."    crnd " crnd @ . cr
  ."    vval " vval @ . cr
  cr ;

: pickNext ( -- crnd + |N| )
    crnd @ |N| + ;

: pickNext! ( -- old_crnd ; crnd = crnd + |N| )
    crnd @ pickNext crnd ! ;

: paxos.eth.type.learn
    s" TYPE=LEARN" ;

: paxos.pack32 ( val1 val2 vals -- packed )
    drop drop drop s" PACKED" ;

: paxos.eth.packet
    append ;

: openflow.flood ( packet -- )
    ." Flooding: " type cr ;

: paxos.learn ( addr n v -- Ethernet packet )
    2 paxos.pack32
    paxos.eth.type.learn
    swap paxos.eth.packet ;

: on_accept ( n v -- )
    swap dup
    crnd @ >= if
      dup crnd !
      over vval !
      swap

      dup2 mac.s1 paxos.learn openflow.flood
    else
      drop drop
    then ;

begin.main
  ( s" ho" paxos.eth.type.learn s" PAYLOAD" paxos.eth.packet type cr )
  pickNext! . cr
  pickNext! . cr
  pickNext! . cr
  pickNext! . cr
  pickNext! . cr
end.main

." Stack at end of run: "
.s cr
