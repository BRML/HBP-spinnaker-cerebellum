from __builtin__ import max
from pacman103.core.process_bar import ProgressBar
__author__ = 'stokesa6'
import logging
import inspect

from pacman103.lib import graph
from pacman103.core import reports
from pacman103 import conf
from pacman103.lib import lib_map
from pacman103.core.mapper import placer_algorithms
from pacman103.core.mapper.partitioner_algorithms.abstract_partitioner import AbstractPartitioner

logger = logging.getLogger( __name__ )

class PartitionAndPlacePartitioner(AbstractPartitioner):
    
    def __init__(self, dao):
        
        self.dao = dao
        #locate the chosen placer
        placer_algorithms_list = dict(
        map( lambda (name, placer) : (name.replace("Placer",""),placer),
            inspect.getmembers(placer_algorithms, inspect.isclass)
        ))
        
        try:
            placer_class = placer_algorithms_list[
                        conf.config.get("Placer", "algorithm")]
            self.placer = placer_class(dao)
        except KeyError as e:
            raise ValueError("Invalid partitioner algorithm specified. "
                              " I don't know '%s'." % e)
            
        self.progress = None

    def partition(self):
        """
        Loads machine and vertex objects from the datastore, calls
        :py:func:`pacman103.core.mapper.partition_raw` to generate subvertices
         and subedges, and stores them in the datastore.

        :param `pacman103.core.dao` dao:
            datastore containing machine and vertex objects.
        """
        # locate correct placer

        logger.info("* Running Partitioner and Placer as one *")
        
        # Load the machine and vertices objects from the dao
        machine = self.dao.get_machine()
        vertices = self.dao.get_vertices()
        
        #calculate time steps
        no_machine_time_steps = None
        if self.dao.run_time is not None:
            no_machine_time_steps = \
                int((self.dao.run_time * 1000.0) / self.dao.machineTimeStep)
        machine_time_step_us = self.dao.machineTimeStep

        # Partition the vertices into subvertices and consequent subedges
        subvertices, subedges, placements = \
            self.partition_raw(machine, vertices,no_machine_time_steps,
                               machine_time_step_us, self.placer)

        # Store the results in the dao
        self.dao.set_subvertices(subvertices)
        self.dao.set_subedges(subedges)
        self.dao.set_placements(placements)
        
        #update dao so that controller only calls the next stack aspect
        self.dao.done_partitioner = True
        self.dao.done_placer = True
        
    def find_max_ratio(self, resources, max_resources):
        '''
        helper method for finding the max ratio for a resoruces
        '''
        cpu_ratio = (float(resources.clock_ticks) 
                / float(max_resources.clock_ticks))
        dtcm_ratio = (float(resources.dtcm) / float(max_resources.dtcm))
        sdram_ratio = (float(resources.sdram) / float(max_resources.sdram)) 
        return max((cpu_ratio, dtcm_ratio, sdram_ratio))

    def partition_raw(self, machine, vertices, no_machine_time_steps,
                      machine_time_step_us, placer):
        '''
        entry method for partitioning
        '''
        placements = list()
        subvertices = list()

        #sort out vertex's by constraints
        sort = lambda vertex: vertex.constraints.placement_cardinality
        vertices = sorted(vertices, key=sort, reverse=True)
        
        n_atoms = 0
        for vertex in vertices:
            n_atoms += vertex.atoms
        self.progress = ProgressBar(n_atoms)
        self.partitioned = dict()

        # Partition one vertex at a time
        for vertex in vertices:
            #only partition real vertexes. virtual ones are ignored
            if vertex.is_virtual():
                self.partition_virtual_vertexes(vertex, placements,
                                                subvertices, placer)
            elif len(vertex.subvertices) == 0:
                self.partition_vertexes(vertex, no_machine_time_steps,
                                        machine_time_step_us, subvertices,
                                        placer, placements)
            else:
                print "Vertex {} is already partitioned!".format(vertex.label)
        self.progress.end()
    
        subedges = self.generate_sub_edges(subvertices)
        
        return subvertices, subedges, placements
    
    def get_max_atoms_per_core(self, vertices):
        
        max_atoms_per_core = 0
        for v in vertices:
            max_for_vertex = v.get_maximum_atoms_per_core()
                
            # If there is no maximum, the maximum is the number of atoms
            if max_for_vertex is None:
                max_for_vertex = v.atoms
    
            # Override the maximum with any custom maximum
            if v.custom_max_atoms_per_core is not None:
                max_for_vertex = v.custom_max_atoms_per_core
            
            max_atoms_per_core = max(max_atoms_per_core, max_for_vertex)
        return max_atoms_per_core

    def partition_vertexes(self, vertex, no_machine_time_steps,
                           machine_time_step_us, subvertices, placer,
                           placements):
        '''
        partitions normal vertexes
        '''
        
        vertices = list()
        vertices.append(vertex)
        extra_vertices = vertex.get_partition_dependent_vertices()
        if extra_vertices is not None:
            for v in extra_vertices:
                if v.atoms != vertex.atoms:
                    raise Exception("A vertex and its partition-dependent"
                            + " vertices must have the same number of atoms")
                vertices.append(v)
                    
        
        # Prepare for partitioning, getting information
        partition_data_objects = [v.get_partition_data_object() 
                for v in vertices]
        max_atoms_per_core = self.get_max_atoms_per_core(vertices)
        
        self.partition_by_atoms(vertices, placer, vertex.atoms, 
                max_atoms_per_core, no_machine_time_steps, machine_time_step_us,
                partition_data_objects, subvertices, placements)

    def partition_by_atoms(self, vertices, placer, n_atoms, 
            max_atoms_per_core, no_machine_time_steps, machine_time_step_us,
            partition_data_objects, subvertices, placements):
        '''
        tries to partition subvertexes on how many atoms it can fit on
        each subvert
        '''
        n_atoms_placed = 0
        while n_atoms_placed < n_atoms:
            
            #logger.debug("Maximum available resources for "
            #             "partitioning: {}".format(resources))

            lo_atom = n_atoms_placed
            hi_atom = lo_atom + max_atoms_per_core - 1
            if hi_atom >= n_atoms:
                hi_atom = n_atoms - 1

            # Scale down the number of atoms to fit the available resources
            used_placements, hi_atom = self.scale_down_resources( 
                    lo_atom, hi_atom, vertices,
                    no_machine_time_steps, machine_time_step_us,
                    partition_data_objects, placer,
                    max_atoms_per_core)

            # Update where we are
            n_atoms_placed = hi_atom + 1
            
            # Create the subvertices and placements
            for (vertex, _, x, y, p, used_resources, _) in used_placements:
                            
                subvertex = graph.Subvertex(vertex, lo_atom, hi_atom, 
                        used_resources)
                processor = self.dao.machine.get_processor(x, y, p)
                placement = lib_map.Placement(subvertex, processor)
                
                subvertices.append(subvertex)
                placements.append(placement)
            
            no_atoms_this_placement = (hi_atom - lo_atom) + 1
            self.progress.update(no_atoms_this_placement)

    def scale_down_resources(self, lo_atom, hi_atom, vertices, 
            no_machine_time_steps, machine_time_step_us, 
            partition_data_objects, placer, max_atoms_per_core):
        '''
        reduces the number of atoms on a core so that it fits within the
        resoruces avilable
        '''
        
        # Find the number of atoms that will fit in each vertex given the
        # resources available
        used_placements = list()
        min_hi_atom = hi_atom
        for i in range(len(vertices)):
            vertex = vertices[i]
            partition_data_object = partition_data_objects[i]
            
            resources = placer.get_maximum_resources(vertex.constraints)
            used_resources = vertex.get_resources_for_atoms(lo_atom, hi_atom,
                no_machine_time_steps, machine_time_step_us, 
                partition_data_object)
            ratio = self.find_max_ratio(used_resources, resources)
            
            while ratio > 1.0 and hi_atom >= lo_atom:
    
                # Scale the resources by the ratio
                old_n_atoms = (hi_atom - lo_atom) + 1
                new_n_atoms = int(float(old_n_atoms) / ratio)
    
                # Avoid looping
                if old_n_atoms == new_n_atoms:
                    new_n_atoms -= 1
                else:
                    # Subtract a tenth of the difference between the old
                    # and new
                    new_n_atoms -= int((old_n_atoms - new_n_atoms) / 10.0)
    
                # Find the new resource usage
                hi_atom = lo_atom + new_n_atoms - 1
                used_resources = \
                    vertex.get_resources_for_atoms(lo_atom, hi_atom,
                                                   no_machine_time_steps,
                                                   machine_time_step_us,
                                                   partition_data_object)
                ratio = self.find_max_ratio(used_resources, resources)
              
            # If we couldn't partition, raise and exception
            if hi_atom < lo_atom:
                raise Exception("Vertex {} could not be partitioned".format(
                        vertex.label))
                
            # Try to scale up until just below the resource usage
            used_resources, hi_atom = self.scale_up_resource_usage(
                    used_resources, hi_atom, lo_atom, 
                    max_atoms_per_core, vertex, no_machine_time_steps, 
                    machine_time_step_us, partition_data_object, resources, 
                    ratio)
            
            # If this hi_atom is smaller than the current, minimum update the
            # other placements to use (hopefully) less resources 
            if hi_atom < min_hi_atom:
                min_hi_atom = hi_atom
                new_used_placements = list()
                for (v, part_obj, x, y, p, v_resources, resources) in used_placements:
                    placer.unplace_subvertex(x, y, p, v_resources)
                    new_resources = v.get_resources_for_atoms(lo_atom, 
                            min_hi_atom, no_machine_time_steps,
                            machine_time_step_us, part_obj)
                    (new_x, new_y, new_p) = placer.place_subvertex(
                            new_resources, v.constraints)
                    new_used_placements.append(v, part_obj, new_x, new_y, new_p,
                            new_resources, resources)
                used_placements = new_used_placements
                
            # Place the vertex
            x, y, p = placer.place_subvertex(used_resources, 
                    vertex.constraints)
            used_placements.append((vertex, partition_data_object, x, y, p, 
                    used_resources, resources))
            
        return used_placements, min_hi_atom


    def scale_up_resource_usage(self, used_resources, hi_atom, lo_atom, 
                        max_atoms_per_core, vertex, no_machine_time_steps,
                        machine_time_step_us, partition_data_object, resources,
                        ratio):
        '''
        tries to psuh the number of atoms into a subvertex as it can
         with the estimates
        '''
        
        previous_used_resources = used_resources
        previous_hi_atom = hi_atom
        while ((ratio < 1.0) and ((hi_atom + 1) < vertex.atoms)
                and ((hi_atom - lo_atom + 2) < max_atoms_per_core)):

            #logger.debug("Scaling up - Current subvertex from"
            #    " %d to %d of %d, ratio = %f, resources = %s" % (lo_atom,
            #             hi_atom, no_atoms, ratio, used_resources))

            previous_hi_atom = hi_atom
            hi_atom += 1

            # Find the new resource usage
            previous_used_resources = used_resources
            used_resources = \
                vertex.get_resources_for_atoms(lo_atom, hi_atom,
                                               no_machine_time_steps,
                                               machine_time_step_us,
                                               partition_data_object)
            ratio = self.find_max_ratio(used_resources, resources)
        return previous_used_resources, previous_hi_atom


    def partition_virtual_vertexes(self, vertex, placements, subvertices,
                                   placer):
        '''
        handle the paritioning of virtual vertexes
        '''
        #ask the vertex how many sub verts to split it into to.
        number_of_sub_verts = vertex.split_into_subvertex_count()
        number_per_subvert = vertex.atoms / number_of_sub_verts
        for subvert_count in range(number_of_sub_verts):
            
            #create a subvert
            start = (subvert_count * number_per_subvert)
            end = start + number_per_subvert - 1
            subvertex = graph.Subvertex(vertex, start, end, 0)
            subvertices.append(subvertex)
            
            # Update the constraint to reflect changes if there are
            # more than 1 subvert
            if vertex.constraints.p is not None:
                start_constraint = \
                    lib_map.VertexConstraints(vertex.constraints.x,
                        vertex.constraints.y,
                        vertex.constraints.p + subvert_count)
            else:
                start_constraint = vertex.constraints
            
            # Place the subvertex
            chip = self.dao.machine.get_chip(vertex.constraints.x,
                    vertex.constraints.y)
            x, y, p = placer.place_virtual_subvertex(start_constraint,
                    chip.get_processors())
            processor = self.dao.machine.get_processor(x, y, p)
            placement = lib_map.Placement(subvertex, processor)
            placements.append(placement)
        self.progress.update(vertex.atoms)
            
    #goes though the vertexes and generates subedges for all outcoming edges
    def generate_sub_edges(self, subvertices):
        '''
        Partition edges according to vertex partitioning
        '''
        subedges = list()
        for src_sv in subvertices:
            # For each out edge of the parent vertex...
            for edge in src_sv.vertex.out_edges:
                # ... and create and store a new subedge for each postsubvertex
                for dst_sv in edge.postvertex.subvertices:
                    #logger.debug(
                    #        "Creating subedge between {} ({}-{}) and {} ({}-{})"
                    #        .format(src_sv.vertex.label, src_sv.lo_atom, 
                    #                src_sv.hi_atom, dst_sv.vertex.label,
                    #                dst_sv.lo_atom, dst_sv.hi_atom))
                    subedge = edge.create_subedge(src_sv, dst_sv)
                    subedges.append(subedge)
                    
        return subedges
