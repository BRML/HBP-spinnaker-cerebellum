import logging
logger = logging.getLogger( __name__ )
from pacman103.lib import graph
from pacman103.core.mapper.partitioner_algorithms.abstract_partitioner import AbstractPartitioner

class BasicPartitioner(AbstractPartitioner):
    
    def __init__(self, dao):
        self.dao = dao

    def partition(self):
        """
        Loads machine and vertex objects from the datastore, calls
        :py:func:`pacman103.core.mapper.partition_raw` to generate subvertices and
        subedges, and stores them in the datastore.

        :param `pacman103.core.dao` dao:
            datastore containing machine and vertex objects.
        """
        logger.info("* Running Partitioner *")
        # Load the machine and vertices objects from the dao
        machine = self.dao.get_machine()
        vertices = self.dao.get_vertices()
        #calculate different time steps
        no_machine_time_steps = None
        if self.dao.run_time is not None:
            no_machine_time_steps = int((self.dao.run_time * 1000.0) 
                    / self.dao.machineTimeStep)
        
        machine_time_step_us = self.dao.machineTimeStep
        # Partition the vertices into subvertices and consequent subedges
        subvertices, subedges = self.partition_raw(machine, vertices,
                                           no_machine_time_steps,
                                           machine_time_step_us)
        # Store the results in the dao
        self.dao.set_subvertices(subvertices)
        self.dao.set_subedges(subedges)
        
        #update dao so that controller only calls the next stack aspect
        self.dao.done_partitioner = True

    def partition_raw(self, machine, vertices, no_machine_time_steps,
                      machine_time_step_us):
        """
        Generates subvertices from vertices according to their resource requirements
        and the resource availability of processors in the machine, and then
        generates subedges between all subvertices whose parent vertices are
        connected by edges. Resources and requirements are specified per atom in
        terms of processor cycles per millisecond, processor memory, and chip
        memory. The number of atoms that may be placed on a processor (and therefore
        the number and size of subvertices produced) is found by dividing the
        available resources per processor by the required resources of an atom.

        *Side effects*:
            updates each vertex with references to its child subvertices.

        **TODO**:
            check that generated subvertices do not violate the placement
            constraints of the parent vertex.

        :param `pacman103.lib.lib_machine.Machine` machine:
            machine from which to read processor resource availability.
        :param list vertices:
            list of :py:class:`pacman103.lib.graph.Vertex` instances to
            partition into subvertices.

        :returns:
            tuple comprising a list of :py:class:`pacman103.lib.graph.Subvertex`
            instances and a list of :py:class:`pacman103.lib.graph.Subedge`
            instances.
        """
        subvertices = list()
        subedges = list()

        # Partition one vertex at a time
        for vertex in vertices:
            if not vertex.is_virtual():
                # Compute atoms per core from resource availability
                partition_object = vertex.get_partition_data_object()
                partition_object, requirements = vertex.get_resources_for_atoms(
                        0, 1, no_machine_time_steps, machine_time_step_us,
                        partition_object)

                availability = machine.get_maximum_resources_per_processor(vertex.constraints)
                apc_sd = availability.resources[2] / requirements.resources[2]
                apc_dt = availability.resources[1] / requirements.resources[1]
                apc_cp = availability.resources[0] / requirements.resources[0]

                # Check for any model-specific constraint on atoms per core and use
                # it, if it's more constraining than the current apc value:
                model_name = vertex.model_name

                max_atoms_per_core = vertex.get_maximum_atoms_per_core()
                apc = min(max_atoms_per_core, apc_sd, apc_dt, apc_cp)

                # Partition into subvertices
                counted = 0
                while counted < vertex.atoms:
                    # Determine subvertex size
                    remaining = vertex.atoms - counted
                    if remaining > apc: alloc = apc
                    else:               alloc = remaining
                    # Create and store new subvertex, and increment elements counted
                    subvert = graph.Subvertex(vertex, counted, counted + alloc - 1,
                            vertex.get_resources_for_atoms(counted, counted + alloc - 1))
                    subvertices.append(subvert)
                    counted = counted + alloc


        # Partition edges according to vertex partitioning
        for src_sv in subvertices:
            # For each out edge of the parent vertex...
            for edge in src_sv.vertex.out_edges:
                # ... and create and store a new subedge for each postsubvertex
                for dst_sv in edge.postvertex.subvertices:
                    subedge = edge.create_subedge(src_sv, dst_sv)
                    subedges.append(subedge)

        return subvertices, subedges
