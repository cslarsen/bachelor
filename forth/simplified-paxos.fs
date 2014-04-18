\ Simplified Paxos algorithm
\ 
\ Comments on variables first state which ROLE they belong to,
\ then what they contain.  This is just for book keeping, as
\ each node takes on all roles.

variable crnd \ PROPOSER: Current round number (unique for system)
variable n_id \ NODE: Node ID
variable rnd  \ ACCEPTOR: Highest round seen
variable vval \ ACCEPTOR: Value last accepted (values are packet IDs)
variable |N|  \ NODE: Number of Paxos nodes in system

\ Convenience constants
variable true
variable false

: pickNext ( -- crnd + |N| )
    crnd @ |N| @ + ;

: pickNext! ( -- crnd + |N| ; also sets crnd )
    pickNext dup crnd ! ;

: pickNext!! ( -- crnd ; set crnd to new value, return old value )
    crnd @ pickNext! drop ;

\ Initialize this Paxos node
: init-node ( -- )
    3 |N| ! \ Three Paxos nodes
    0 n_id ! \ Node id
    n_id @ crnd ! \ crnd = node id
    0 rnd ! \ Initialize rnd to 0
    -1 true !
    0 false !
    ;

: on-accept ( n v -- )
    over dup ( n v -- v n n )
    rnd @ >= if ( v n n -- v n ; if n >= rnd )
        rnd ! ( v n -- v )
        vval ! ( v -- )
        true @ \ Return value, GO AHEAD (all bits 1)
    else
        drop drop ( v n -- )
        false @ \ Return value, STOP
    then ;

init-node
