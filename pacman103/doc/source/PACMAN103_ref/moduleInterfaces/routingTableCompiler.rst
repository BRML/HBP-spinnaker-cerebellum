
.. _RoutingTableCompilerInterfaces:

Routing Table Compiler
----------------------

This function has not yet been implemented.

It should receive as input a list of chips and should iterate through
them, building a router table file for each one, using the chipID.router
object for each one. this object provides a list of RoutingEntry objects
that have been compiled by the router() function during the Route process.

In the simplest implementation, these entries are translated one-to-one
to create entries for the router which are then converted to a format ready
for loading.

A more intelligent implementation would combine router entries to eliminate
unnecessary or duplicate entries (not yet implemented).

<TODO>

