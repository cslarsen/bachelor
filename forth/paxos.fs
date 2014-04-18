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
    \ This should always hold:
    \ pickNext!! |N| @ mod n_id @ =
    \ Or: crnd mod |N| == n_id

\ Initialize this Paxos node
: init-node ( num-nodes node-id -- )
    n_id !      \ Set node ID
    |N| !       \ Set number of Paxos nodes

    n_id @ crnd ! \ Set crnd to node ID
    0 rnd !       \ Initialize rnd to 0

    -1 true !     \ All bits set
    0 false !     \ All bits unset
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

\ Initialize with 3 Paxos nodes and node ID of zero
3 0 init-node
