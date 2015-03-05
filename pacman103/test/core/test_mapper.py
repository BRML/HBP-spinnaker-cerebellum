#!/usr/bin/env python
import unittest
from pacman103.core.mapper.partitioner_algorithms import basic_partitioner

from pacman103.front import pynn
import pacman103.core.exceptions as exceptions
from pacman103.lib import graph
import pacman103.lib.machine.machine as lib_machine
#import pacman103.core.mapper as mapper
import pacman103.core.mapper.placer as placer
from pacman103.front import pynn
from pacman103.core.mapper.routing_algorithms import dijkstra_routing
import pdb

class PartitionTestCase(unittest.TestCase):
    """
    Tests for the pacman103.core.mapper.partition_raw function.
    """


    def test_parition_production_with_zero_atoms(self):
        """
        Tests for the pacman103.core.mapper.partition_raw function.
        """
        atoms = 0

        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
        vertices = [graph.Vertex(atoms, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

        # subvertices and subedges should be zero
        self.assertEqual((subvertices,subedges),([],[]))

        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

    def test_parition_production_with_one_atom(self):
        """
        Tests for the pacman103.core.mapper.partition_raw function.
        """
        atoms = 1

        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
        vertices = [graph.Vertex(atoms, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)


        # subvertices should have only one vertex since all atoms fit in a
        # core
        self.assertEqual(len(subvertices),1)
        # subedges should be zero
        self.assertEqual(subedges,[])
        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)


    def test_partition_production_with_no_subvertices(self):
        """
        Calculates max atoms per vertex based on the vertex model and then
        it checks if the subvertices are an instance of graph.Subvertex,
        if total number of subvertices is one and if th subedges are zero.
        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        vertices = [graph.Vertex(atoms, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

        # subvertices should have only one vertex since all atoms fit in a
        # core
        self.assertEqual(len(subvertices),1)

        # subedges should be zero
        self.assertEqual(subedges,[])

    def test_partition_production_with_two_subvertices(self):
        """
        Calculates max atoms per vertex based on the vertex model and then
        it adds one more atom in to create a subvertex.
        This test checks if the subvertices are an instance of graph.Subvertex,
        if total number of subvertices is two and if the subedges are zero.

            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        vertices = [graph.Vertex(atoms+1, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

        # subvertices should have only two vertices since all atoms won't fit in a
        # core
        self.assertEqual(len(subvertices),2)

        # subedges should be zero
        self.assertEqual(subedges,[])

    def test_partition_production_with_two_subverticesb(self):
        """
        Calculates max atoms per vertex based on the vertex model and then
        it adds twice that number minus one to create two subvertices.
        This test checks if the subvertices are an instance of graph.Subvertex,
        if total number of subvertices is two and if the subedges are zero.

        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        vertices = [graph.Vertex((atoms*2)-1, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

        # subvertices should have only two vertices since all atoms fit in two
        # cores
        self.assertEqual(len(subvertices),2)

        # subedges should be zero
        self.assertEqual(subedges,[])


    def test_partition_production_with_two_subvertices_full(self):
        """
            Calculates max atoms per vertex based on the vertex model and then
            it adds twice that number to create two full-sized subvertices.
            This test checks if the subvertices are an instance of graph.Subvertex,
            if total number of subvertices is two and if the subedges are zero.

            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        vertices = [graph.Vertex(atoms*2, pynn.IF_curr_exp)]
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)
        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

        # subvertices should have only two vertices since all atoms fit in two
        # cores
        self.assertEqual(len(subvertices),2)

        # subedges should be zero
        self.assertEqual(subedges,[])

    def test_partition_production_with_a_number_of_subverticesa(self):
        """
            Calculates max atoms per vertex based on the vertex model and then
            it tests multiples of that number.
            This test checks if the subvertices are an instance of graph.Subvertex,
            if total number of subvertices is two and if the subedges are zero.

            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        for i in range(16):
            vertices = [graph.Vertex(atoms*i, pynn.IF_curr_exp)]
            max_atoms_per_core = dict()
            subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

            # subvertices should be an instance of the Subvertex class
            for subvertex in subvertices:
                self.assertIsInstance(subvertex, graph.Subvertex)

            # subvertices should have only two vertices since all atoms fit in two
            # cores
            self.assertEqual(len(subvertices),i)

            # subedges should be zero
            self.assertEqual(subedges,[])

    def test_partition_production_with_a_number_of_subverticesb(self):
        """
            Calculates max atoms per vertex based on the vertex model and then
            it tests multiples of that number +1 in order to always create one vertex.
            This test checks if the subvertices are an instance of graph.Subvertex,
            if total number of subvertices is two and if the subedges are zero.

            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')

        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        for i in range(16):
            vertices = [graph.Vertex( (atoms*i)+1 , pynn.IF_curr_exp)]
            max_atoms_per_core = dict()
            subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

            # subvertices should be an instance of the Subvertex class
            for subvertex in subvertices:
                self.assertIsInstance(subvertex, graph.Subvertex)

            # subvertices should have only two vertices since all atoms fit in two
            # cores
            self.assertEqual(len(subvertices),i+1)

            # subedges should be zero
            self.assertEqual(subedges,[])


    def test_partition_production_with_self_projected_edge(self):
        """            
            Calculates max atoms per vertex based on the vertex model and then
            it creates a vertex and adds an edge which projects back to itself.
            This test checks if the subvertices are an instance of graph.Subvertex,
            subedges are an instance of graph.SubEdge
            if total number of subvertices and subedges is 1.
            
            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
        
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements
        
        vertex1 = graph.Vertex(atoms, pynn.IF_curr_exp)

        pdb.set_trace
        edge = graph.Edge(None,vertex1,vertex1)
        max_atoms_per_core = dict()
        subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, [vertex1], max_atoms_per_core)

        # subvertices should be an instance of the Subvertex class
        for subvertex in subvertices:
            self.assertIsInstance(subvertex, graph.Subvertex)

        # subedges should be an instance of the Subvedge class
        for subedge in subedges:
            self.assertIsInstance(subedge, graph.Subedge)

        # subvertices should have only two vertices since all atoms fit in two
        # cores
        self.assertEqual(len(subvertices),1)
    
        # subedges should be zero
        self.assertEqual(len(subedges),1)

    
    def test_partition_production_with_multiple_subvertices_and_self_projected_subedges(self):
        """
            Calculates max atoms per vertex based on the vertex model and then
            it creates a vertex with n multiples of max atoms and adds an edge which projects 
            back to itself. This test checks if the subvertices are an instance of 
            graph.Subvertex, subedges are an instance of graph.SubEdge
            if total number of subvertices and subedges is 1.
            
            """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
        
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements
        
        
        for i in range(16):
            vertex1 = graph.Vertex(atoms*(i+1), pynn.IF_curr_exp)
            
            # Generate a self projected edge
            edge = graph.Edge(None,vertex1,vertex1)
            max_atoms_per_core = dict()
            subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, [vertex1], max_atoms_per_core)
        
            # subvertices should be an instance of the Subvertex class
            for subvertex in subvertices:
                self.assertIsInstance(subvertex, graph.Subvertex)
        
            # subedges should be an instance of the Subvedge class
            for subedge in subedges:
                self.assertIsInstance(subedge, graph.Subedge)
        
            # subvertices are equal to the number of i+1
            self.assertEqual(len(subvertices),(i+1))
        
            # subedges should be squared the number of subvertices
            self.assertEqual(len(subedges),(i+1)**2)

                
    def test_partition_production_with_multiple_subvertices_and_self_projected_subedges_part2(self):
        """
        Calculates max atoms per vertex based on a vertex model and then
        it creates a vertex with n multiples +1 of max atoms and adds an edge which projects
        back to itself. This test checks if the subvertices are an instance of
        graph.Subvertex, subedges are an instance of graph.SubEdge
        if total number of subvertices and subedges is 1.
        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
                    
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements
                    
        for i in range(16):
            vertex1 = graph.Vertex((atoms*(i+1))+1, pynn.IF_curr_exp)
            # Generate a self projected edge
            edge = graph.Edge(None,vertex1,vertex1)
            max_atoms_per_core = dict()
            subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, [vertex1], max_atoms_per_core)
                
            # subvertices should be an instance of the Subvertex class
            for subvertex in subvertices:
                self.assertIsInstance(subvertex, graph.Subvertex)
                        
            # subedges should be an instance of the Subvedge class
            for subedge in subedges:
                self.assertIsInstance(subedge, graph.Subedge)
                        
            # subvertices are equal to the number of i+1
            self.assertEqual(len(subvertices),(i+2))
                        
            # subedges should be squared the number of subvertices
            self.assertEqual(len(subedges),(i+2)**2)


    def test_partition_production_with_multiple_subvertices_and_edges_partA(self):
        """
        Calculates max atoms per vertex based on a vertex model and then
        it creates two vertices. Vertex1 has a multiple of max atoms per core while the size of
        vertex2 stays fixed to max atoms per core.
        This test checks if the subvertices are an instance of
        graph.Subvertex, subedges are an instance of graph.SubEdge
        if total number of subvertices is n+2 and subedges is n+1.
        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
                    
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements

        
        for i in range(16):
            vertex1 = graph.Vertex(atoms*(i+1), pynn.IF_curr_exp)
            vertex2 = graph.Vertex(atoms, pynn.IF_curr_exp)

            # Generate a self projected edge
            edge = graph.Edge(None,vertex1,vertex2)
            max_atoms_per_core = dict()
            subvertices1, subedges1 = basic_partitioner.BasicPartitioner.partition_raw(machine, [vertex1, vertex2], max_atoms_per_core)
            #pdb.set_trace()
            # subvertices should be an instance of the Subvertex class
            for subvertex in subvertices1:
                self.assertIsInstance(subvertex, graph.Subvertex)
                    
            # subedges should be an instance of the Subvedge class
            for subedge in subedges1:
                self.assertIsInstance(subedge, graph.Subedge)
                
            # subvertices should be 1
            self.assertEqual(len(subvertices1),i+2)
                        
            # subedges should be squared the number of subvertices
            self.assertEqual(len(subedges1),(i+1))


    def test_partition_production_with_multiple_subvertices_and_multiple_subedges(self):
        """
        Calculates max atoms per vertex based on a vertex model and then
        it creates two vertices. Vertex2 has a multiple of max atoms per core controlled by i
        while the size of
        vertex1 stays fixed to max atoms per core.
        This test checks if the subvertices are an instance of
        graph.Subvertex, subedges are an instance of graph.SubEdge
        if total number of subvertices is n+2 and subedges is n+1.
        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'unwrapped')
                    
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements
                    
        for i in range(16):
            for j in range(16):
                vertex1 = graph.Vertex(atoms*(i+1), pynn.IF_curr_exp)
                vertex2 = graph.Vertex(atoms*(j+1), pynn.IF_curr_exp)
                        
                # Generate a self projected edge
                edge = graph.Edge(None,vertex1,vertex2)
                max_atoms_per_core = dict()
                subvertices1, subedges1 = basic_partitioner.BasicPartitioner.partition_raw(machine, [vertex1, vertex2], max_atoms_per_core)
            
                # subvertices should be an instance of the Subvertex class
                for subvertex in subvertices1:
                    self.assertIsInstance(subvertex, graph.Subvertex)
                        
                # subedges should be an instance of the Subvedge class
                for subedge in subedges1:
                        self.assertIsInstance(subedge, graph.Subedge)
                        
                # subvertices should be 1
                self.assertEqual(len(subvertices1),i+j+2)
        
                # subedges should be squared the number of subvertices
                self.assertEqual(len(subedges1),(i+1)*(j+1))
                
                
    def test_partition_multiple_productions_with_multiple_subvertices_and_multiple_subedges(self):
        """
        Calculates max atoms per vertex based on a vertex model and then
        it creates 48 pre vertices and 48 pro vertices. 
        This test checks if the subvertices are an instance of
        graph.Subvertex, subedges are an instance of graph.SubEdge
        if total number of subvertices (is i+j+2)*48 and subedges is (i+1)*(j+1)*48*48.
        """
        # Specify a SpiNNaker machine
        machine = lib_machine.Machine('test', 1, 1, 'wrapped')
                    
        # Calculate the max atoms per core
        # The following code has been taken from core.mapper.partition_raw
        requirements = pynn.IF_curr_exp.get_requirements_per_atom()
        resources = machine.get_resources_per_processor()
        atoms = resources / requirements
                    
        print "Long Test: (test_partition_multiple_productions_with_multiple_subvertices_and_multiple_subedges)"
        for i in range(16): # i is the number of subvertices of a prev vertex 
            print "   progress: set",i+1,"of 16"
            for j in range(16): # j is the number of subvertices of a pro vertex
                preVertices = []
                proVertices = []
                for k in range(48): # k is the number of vertices
                    preVertices.append(graph.Vertex(atoms*(i+1), pynn.IF_curr_exp))
                    proVertices.append(graph.Vertex(atoms*(j+1), pynn.IF_curr_exp))
                for k1 in range(48):
                    for k2 in range(48):
                        edges = graph.Edge(None,preVertices[k1],proVertices[k2])
                max_atoms_per_core = dict()
                subvertices, subedges = \
                    basic_partitioner.BasicPartitioner.partition_raw(machine, preVertices + proVertices, max_atoms_per_core)
                
                # subvertices should be an instance of the Subvertex class
                for subvertex in subvertices:
                    self.assertIsInstance(subvertex, graph.Subvertex)
                        
                # subedges should be an instance of the Subvedge class
                for subedge in subedges:
                        self.assertIsInstance(subedge, graph.Subedge)
                        
                # subvertices should be (i+1+j+1)*48
                self.assertEqual(len(subvertices),(i+j+2)*48)
        
                # subedges should be number of preSubvertices times number of proSubvertices
                self.assertEqual(len(subedges),(i+1)*(j+1)*48*48)
                #print i+1, j+1


class PlaceTestCase(unittest.TestCase):
    """
    Tests for the pacman103.core.mapper.place function.
    """

    def test_palloc_exception(self):
        """
        Generates more subvertices than can be placed on the machine and checks
        that a PallocException is thrown.
        """
        # Set up a record of the exception (not) thrown
        exception = None

        with self.assertRaises(exceptions.PallocException):
            # Set dimensions of machine and processor-overload count
            x, y = 1, 1
            overload = x * y * 16 + 1
            # Make a machine with 16 processors
            machine = lib_machine.Machine('test', x, y, 'unwrapped')
            # Make a vertex to split into subvertices
            vertex = graph.Vertex(overload, None)
            # Split vertex into 17 subvertices
            subvertices = list()
            for i in xrange(overload):
                subvertex = graph.Subvertex(vertex, i, i)
                subvertices.append(subvertex)
            # Call parition raw to generate PallocException
            placer.Placer.place_raw(machine, subvertices)

    def test_place_zero_subvertices(self):
        """
        Perform place with no sub-vertices. No exception expected.
        """
        # Set up a record of the exception (not) thrown
        exception = None

        # Set dimensions of machine and processor-load count
        x, y = 1, 1
        load = 1
        # Make a machine with 16 processors
        machine = lib_machine.Machine('test', x, y, 'unwrapped')
        # Construct empty subvertex list:
        subvertices = list()
        # Call partition raw which should generate no exception:
        placer.Placer.place_raw(machine, subvertices)

    def test_place_single_subvertex(self):
        """
        Perform place with only a single sub-vertex
        """
        # Set up a record of the exception (not) thrown
        exception = None

        # Set dimensions of machine and processor-load count
        x, y = 1, 1
        load = 1
        # Make a machine with 16 processors
        machine = lib_machine.Machine('test', x, y, 'unwrapped')
        # Make a vertex to split into subvertices
        vertex = graph.Vertex(load, None)
        # Split vertex into a single subvertex
        subvertex = graph.Subvertex(vertex, 0, 0)
        subvertices = list()
        subvertices.append(subvertex)
        # Call partition raw which should generate no exception:
        placer.Placer.place_raw(machine, subvertices)

    def test_place_valid_core_assignment(self):
        """
        Place a range of designs on machines of different sizes. Are only valid cores used?
        """
        # Set up a record of the exception (not) thrown
        exception = None

        # Set dimensions of machine:
        machine_sizes = [[1,1], [2,2], [4,4], [8,8], [1,8], [8,1]]
        # Try each machine size. Place, then check core assignment. Are all cores valid?
        for m in machine_sizes:
            machine_x, machine_y = m
            load = machine_x * machine_y * 8
            # Make a machine with required number of processors
            machine = lib_machine.Machine('test', machine_x, machine_y, 'unwrapped')
            # Make a vertex to split into subvertices
            vertex = graph.Vertex(load, None)
            # Split vertex into subvertices
            subvertices = list()
            for i in xrange(load):
                subvertex = graph.Subvertex(vertex, i, i)
                subvertices.append(subvertex)
            # Call partition raw which should generate no exception:
            placer.Placer.place_raw(machine, subvertices)
            # Check that every placement was to a valid core:
            for i in subvertices:
                my_x, my_y, my_p = i.placement.processor.get_coordinates()
                self.assertGreaterEqual(my_x, 0, "Placement Exception - outside valid machine x range")
                self.assertGreaterEqual(my_y, 0, "Placement Exception - outside valid machine y range")
                self.assertGreaterEqual(my_p, 1, "Placement Exception - outside valid core range (<1)")
                self.assertLess(my_x, machine_x, "Placement Exception - outside valid machine x range")
                self.assertLess(my_y, machine_y, "Placement Exception - outside valid machine y range")
                self.assertLess(my_p, 17, "Placement Exception - outside valid core range (>16)")
            # Check that every subvertex got assigned somwhere uniquely:
            usage = []
            for i in subvertices:
                my_x, my_y, my_p = i.placement.processor.get_coordinates()
                my_location = [my_x, my_y, my_p]
                self.assertNotIn(usage, my_location, "Placement Exception - core placement duplicated")
                usage.append(my_location)


class RouteUnconnectedTestCase(unittest.TestCase):
    """
    Tests for the pacman103.core.mapper.route_raw function for the case where
    all virtexes are disconnected
    """

    def test_unconnected_subvirtexes(self):
        """
        Test a system with (possibly) some subvertexes but no subedges between
        them make sure it does nothing.

        XXX: This test assumes that creating a vertex with exactly the number of
        atoms that would completely fill N processors will be partitioned into N
        subvertexes.
        """
        # Create a simple test machine with multiple chips (test that no routes
        # are added internal to each chip or between chips).
        def new_machine():
          return lib_machine.Machine(hostname="m", x = 2, y = 2, type="unwrapped")

        neuron_type = pynn.IF_curr_exp

        # Create a minimal machine to figure out the number of subvirtexes to
        # fill the system.
        machine = new_machine()

        requirements = neuron_type.get_requirements_per_atom()
        resources    = machine.get_resources_per_processor()
        atoms_per_processor = resources / requirements

        num_processors = len(machine.get_processors())

        # Set up systems where the number of atoms fills increasing numbers of
        # processors
        for processors_to_fill in xrange(num_processors):
            # Create a minimal machine
            machine = new_machine()

            # Create a virtex which will be partitioned into a number of
            # subvertexes which fills the required number of processors.
            vertices = [graph.Vertex( atoms_per_processor * processors_to_fill
                                        , neuron_type
                                        )]
            max_atoms_per_core = dict()
            subvertices, subedges = basic_partitioner.BasicPartitioner.partition_raw(machine, vertices, max_atoms_per_core)

            # Check that no routers have any routing entries in the system
            # before routing
            self.assertEqual(sum(len(c.router.cam) for c in machine.get_chips()), 0)

            # Do the routing
            dijkstra_routing.DijkstraRouting.route_raw(machine, subedges)

            # There should still be no entries in the routing tables
            self.assertEqual(sum(len(c.router.cam) for c in machine.get_chips()), 0)



class RouteIntegrityTestBase(object):
    """
    This class should be inherited by various integrity tests which test
    different types of connection schemes. This class implements the tests on an
    arbitarily connected machine. It is not, however, a complete test.
    
    inheriting classes should inherit this and unittest.TestCase implement setUp
    to create a machine with an appropriately connected set of neurons. In
    particular the following should be defined:
    
    * self.machine should contain the machine to be tested
    * self.subverticies should contain a list of the subverticies
    * self.subedges should contain a list of the subedges
    * self.routings should contain a list of Routing objects generated by the
      router.
    
    Utility functions _init_machine_and_vertexes and _partition_place_and_route
    are provided which will do all but the creation of edges between vertices.
    """
    
    
    def test_all_routed(self):
        """
        Test to check that for all subvertexes which have a subedge between
        them, routers are configured correctly to allow a packet to arrive
        there.
        """
        # TODO (i.e. these need writing here, I'm not expecting them to be
        # inherited! Someone get on this!)
        pass
    
    
    def test_no_extra_routes(self):
        """
        Test that no routes exist which are not used by a subedge. This prevents
        the possibility of packets whizzing around which aren't going anywhere.
        """
        # TODO (i.e. these need writing here, I'm not expecting them to be
        # inherited! Someone get on this!)
        pass
    
    
    
    def _init_machine_and_vertexes(self, proportion_occuped_processors = 1.0):
        """
        Utility function: Create a test machine filled with enough verticies
        such that proportion_occuped_processors will be filled. No partitioning,
        placement and routing will have occurred allowing the connectivity of
        the subverticies to be set up.
        
        Sets:
        * self.machine to a machine
        * self.vertices to a list of vertices sized to fill the specified
          proportion of processors
        """
        self.machine = lib_machine.Machine(hostname="m", x = 2, y = 2, type="unwrapped")
        
        # Use this type of neuron for all test vertexes
        neuron_type = pynn.IF_curr_exp
        
        requirements = neuron_type.get_requirements_per_atom()
        resources    = self.machine.get_resources_per_processor()
        atoms_per_processor = resources / requirements
        
        num_processors = len(self.machine.get_processors())
        
        # Create one vertex for each processor we want occupied. Also, make
        # this vertex as big will fit on one processor.
        self.vertices = [graph.Vertex(atoms_per_processor, neuron_type)
                         for _ in xrange(int(num_processors * proportion_occuped_processors))]
    
    
    def _partition_place_and_route(self):
        """
        Perform partitioning, placement and routing for self.machine and
        self.verticies.
        """
        max_atoms_per_core = dict()
        self.subvertices, self.subedges = basic_partitioner.BasicPartitioner.partition_raw( self.machine
                                                              , self.vertices,
                                                              max_atoms_per_core)
        
        placer.Placer.place_raw(self.machine , self.subvertices)
        
        self.routings = dijkstra_routing.DijkstraRouting.route_raw(self.machine , self.subvertices)
    
    
    def setUp(self):
        # This should be overridden!
        raise NotImplementedError()



class RouteIntegrityTestCircular(RouteIntegrityTestBase, unittest.TestCase):
    """
    Test routing integrity for networks connected in a circular path.
    """
    
    def setUp(self):
        # Create a machine with a vertex mapped to each core.
        self._init_machine_and_vertexes(1.0)
        
        # Create a circular connectivity scheme
        for v1, v2 in zip(self.vertices, self.vertices[1:] + [self.vertices[0]]):
            graph.Edge(None, v1, v2)
        
        # Finish off
        self._partition_place_and_route()



class RouteIntegrityTestAllToAll(RouteIntegrityTestBase, unittest.TestCase):
    """
    Test routing integrity for networks connected all-to-all
    """
    
    def setUp(self):
        # Create a machine with a vertex mapped to each core.
        self._init_machine_and_vertexes(1.0)
        
        # Create a connection to all devices
        for v1 in self.vertices:
            for v2 in self.vertices:
                graph.Edge(None, v1, v2)
        
        # Finish off
        self._partition_place_and_route()


if __name__=="__main__":
    unittest.main()
