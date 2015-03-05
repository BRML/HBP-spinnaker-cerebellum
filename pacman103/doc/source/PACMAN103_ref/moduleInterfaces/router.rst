
.. _RouterInterfaces:

Router (Mapper)
---------------

=================== =========================================
    Field                Value
=================== =========================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              route(dao)
 Called by             control.map_model()
 Input data            machine, subedges, from dao
 Calls                 mapper.route_raw()
 Output data           routings (list of :ref:`Routing` objects) added to dao
=================== =========================================

This function establishes routes between all pairs of placed subvertices 
that are joined by a subedge in the specification. The inputs are a machine
description of the target SpiNNaker machine and a list of the subedges
that need to be routed. this data is taken directly from the dao object.

The route() function calls route_raw() to perform the actual routing.

The output of route() is added to the dao before the function returns. It 
consists of a set of routings objects. Each routings object is a list of
:ref:`Routing` objects, one per subedge to be routed.

Each routing object corresponds to one subedge. It is a list of :ref:`RoutingEntry`
objects that indicate the route that must be followed across the machine
from the chip that holds the source subvertex to the chip that holds the
destination subvertex. 

route_raw() Function
********************

This function is called by its parent (wrapper) function route(). It performs 
the actual routing, returning a list of :ref:`Routing` objects.

=================== =========================================
    Field                Value
=================== =========================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              route_raw(machine, subedges)
 Called by             core.route()
 Input data            machine, subedges
 Calls                 None
 Output data           routings (list of :ref:`Routing` objects) 
=================== =========================================



