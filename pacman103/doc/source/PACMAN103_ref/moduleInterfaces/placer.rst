
.. _PlacerInterfaces:

Placer (Mapper)
---------------

=================== =========================================
    Field                Value
=================== =========================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              place(dao)
 Called by             control.map_model()
 Input data            machine, subvertices
 Calls                 place_raw(machine, subvertices)
 Output data           Placement info, added to dao
=================== =========================================

This function takes as input a dao object that is assumed to contain a list
of partitioned :ref:`Subvertex` objects. It also requires a :ref:`Machine` 
object, describing the size and layout of the target SpiNNaker machine.

It calls a sub-function *place_raw()*, which performs the placement, assigning
each subvetex (representing a task to be performed on the machine) to a
given core.

Before it exits, it places in the dao a member variable placements, which is
a list of objects of type :ref:`Placement` returned to it by *place_raw()*.

Place_raw() function
********************

=================== =========================================
    Field                Value
=================== =========================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              place_raw(machine, subvertices)
 Called by             control
 Input data            machine, subvertices
 Calls                 none
 Output data           placements (a list of Placement objects)
=================== =========================================

This function is called by its parent (wrapper) function place(). It performs 
the actual core assignment (placement) for each :ref:`Subvertex` and returns
a list of these (subvertex, core) pairings in a list of :ref:`Placement` objects.


