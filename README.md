Bachelor Thesis for Christian Stigen Larsen
===========================================
This repository contains all the work I've done in writing my thesis.

Contents
========

Makefile.mininet
----------------
Should be copied to the Mininet VM at ~mininet/Makefile.  Contains make
targets that lets one easily bring up various Mininet topologies and various
remote controllers.  Can also be used to easily run benchmarks.

notes/
------
Contains various development notes for OpenFlow, Open vSwitch, etc.

open-vswitch/
-------------
Modified source code for Open vSwitch tailored to this thesis project.

paxos/
------
Contains Mininet topologies, controllers and supporting code for message
handling, logging, etc.

python/
-------
Old repository of Mininet topologies and controllers. Also contains some
simple server software to be used as part of the benchmark, as well as some
Paxos simulations.

thesis/
-------
The complete text of the thesis.

forth/
------
Contains some experiments in using Forth on Open vSwitch. Will probably be
deleted.

Author
======
Thesis, code and Open vSwitch modifications were written by Christian Stigen
Larsen in 2014.

Copyright and license
=====================
Copyright (C) 2014 Christian Stigen Larsen
All rights reserved.

Currently, everything here is not for redistribution, except according to
the rules of University of Stavanger regarding thesis material.

The Open vSwitch modifications, however, can be distributed at will under
its license requirements.

The rest will most likely be distributed under some open source license
after I've polished the code and decided what to publish.
