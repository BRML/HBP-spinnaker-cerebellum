Introduction
************

The Partitioning and Configuration Manager (PACMAN) is the set of software that
runs on a host machine in order to drive SpiNNaker simulations. PACMAN takes
some input from a domain-specific front-end, translates it into a
domain-agnostic representation, maps this representation to the processing and
communication resources of a SpiNNaker board, builds, loads and triggers the
simulation, and retrieves the results.

PACMAN essentially operates on graphs. Domain-specific graphs, such as
descriptions populations of neurons and projections of synapses from PyNN, are
taken from a front-end interface and translated into domain-agnostic graphs of
vertices and edges. These graphs are then mapped onto SpiNNaker machines, by
allocating each vertex to one or more processors that compute vertex state over
time, and allocating each edge to one or more paths across the packet-switched
communications fabric of SpiNNaker.

PACMAN contains six packages:

* :py:mod:`pacman103.core` provides domain-agnostic code that maps models to be
  simulated onto SpiNNaker.
* :py:mod:`pacman103.front` provides code that translates domain-specific models
  into domain-agnostic graphs with which PACMAN may work.
  
  *  :py:mod:`pacman103.front.pynn` provides an interface to PyNN
     (http://neuralensemble.org/trac/PyNN)
  *  :py:mod:`pacman103.front.nengo` (under heavy development) provides
     an interface to Nengo (http://nengo.ca)
  
* :py:mod:`pacman103.lib` contains classes that are instantiated to represent
  the entities with which PACMAN works, such as graph vertices and processors.
* :py:mod:`pacman103.scp` provides code that transmits messages between the host
  machine and SpiNNaker over Ethernet.
* :py:mod:`pacman103.store` contains static descriptions of domain-agnostic
  resources used by PACMAN, such as SpiNNaker machines.
* :py:mod:`pacman103.test` provides regression tests and examples.

Additionally, the :file:`doc` directory contains the project documentation.

The remit of PACMAN103 is to drive simulations on SpiNNaker machines containing
10^3 processors. When it reaches version 1.0 (implying that all feature
requirements have been met and all modules have been thoroughly tested) design
will begin on PACMAN104.
