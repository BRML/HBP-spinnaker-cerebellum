
.. _PartitionerInterfaces:

Partitioner (Mapper)
--------------------

The partition function in the mapper is called by the controller
as part of the process to map the user's specification to the machine.

=================== =========================================================
    Field                Value
=================== =========================================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              partition(dao)
 Called by             control
 Input data            dao object
 Calls                 partition_raw(machine, vertices)
 Output data           subvertices (list of Subvertex object), stored in dao
                       subedges (list of Subedge object), stored in dao
=================== =========================================================

Partition takes the dao object as an input. It calls a sub-function, 
partition_raw, passing a python list of :ref:`Vertex` ready for partitioning.

This partition_raw() function performs the actual partitioning.


Partition_raw() function
************************

=================== =========================================
    Field                Value
=================== =========================================
 Module                mapper
 PACMAN103 file        core/mapper.py
 Function              partition_raw(machine, vertices)
 Called by             control.map_model()
 Input data            machine, vertices
 Calls                 none
 Output data           subvertices (list of Subvertex objects)
                       subedges (list of Subedge objects)
=================== =========================================

This function is called by its parent, wrapper function, partition(). It 
takes a description of the target SpiNNaker machine and a list of the 
vertices (each of type :ref:`Vertex`) from the users specification.

The function returns two lists:

* A list of elements of type :ref:`SubVertex`, created by partitioning the 
  given vertices so as to limit the required resource sufficiently for it to 
  fit on one core.

* A list of elements of type :ref:`Subedge`, created by partitioning the 
  edges incident on the given vertices, connecting the subvertices while 
  maintaining correspondence with the original edges.


