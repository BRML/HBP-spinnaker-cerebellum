from pacman103.lib import lib_map
import operator

class Vertex( object ):
    counter = 0
    custom_max_atoms_per_core = None
    
    """
    Represents a vertex of the input graph.

    :param int atoms: number of atoms in the vertex.
    :param `pacman103.lib.lib_map.VertexConstraints` constraints:
        chip-placement constraints for the mapping stage.
    :param string label: name of the vertex.

    :attribute int flags : Bit wise selection of information to be recorded
                       during simulation.
    :attribute list subvertices : Child vertices after partitioning
    :attribute list in_edges  : Edges with this vertex as a target
    :attribute list out_edges : Edges with this vertex as a source
    """
    def __init__( self, atoms, constraints=None, label=None, virtual=False):
        
        # Record passed parameters
        self.atoms = atoms

        if constraints is None: 
            self.constraints = lib_map.VertexConstraints()
        else:                   
            self.constraints = constraints
        if label == None:
            label = "Vertex {}".format(Vertex.counter)
            Vertex.counter += 1
        self.label = label
        self.virtual = virtual
        self.flags = 0

        # Set up reference lists to subvertices and edges
        self.subvertices = list()
        self.in_edges = list()
        self.out_edges = list()

    '''
    allows tools to determine if a vertex is based off a external device
    '''
    def is_virtual(self):
        return self.virtual

    @property
    def model_name( self ):
        """
        Get the name of the model being represented
        
        :return: The name of the model
        :rtype: string
        """
        raise NotImplementedError
    
    def get_maximum_atoms_per_core(self):
        """
        Get the maximum number of atoms supported on a core for this model
        
        :return: The maximum atoms per core, or None if no maximum
        """
        raise NotImplementedError
    
    def get_partition_data_object(self):
        """
        Get an object that can hold data during partitioning to avoid
        recalculation with multiple calls to get_resources_for_atoms
        
        :return: A data object, or None if not required
        """
        return None
    
    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
            machine_time_step_us, partition_data_object):
        """
        Get the resource requirements for a range of atoms
        
        :param lo_atom: The index of the start of the range
        :param hi_atom: The index of the end of the range
        :param no_machine_time_steps: The number of machine time steps that will
                                    be executed by the run
        :param machine_time_step_us: The number of microseconds per times step 
        :param partition_data_object: An object returned by 
                                    get_partition_data_object
        :return: a Resources object with the appropriate values
        :rtype: lib_map.Resources
        """
        raise NotImplementedError
    
    def get_partition_dependent_vertices(self):
        """
        Gets a list of vertices that should be partitioned the same as this
        vertex, or None if there are no such vertices
        Note that every vertex should have exactly the same number of atoms,
        and every returned vertex should either also return this vertex in
        this list of its partition-dependent vertices, or else the dependent
        vertices should not be given to the partitioner separately at all
        """
        return None

    def append_a_new_subvertex(self, subvert):
        """
        Appends a new subvertex to this vertex
        """
        self.subvertices.append(subvert)
    
    def generateDataSpec( self, processor, subvertex, dao ):
        """
        Generates a data specification from a subvertex of this vertex
        
        :param processor: The processor that the subvertex has been allocated
        :param subvertex: The subvertex of the vertex to generate the spec for
        :param dao: The dao containing assignment information 
        :return: a tuple of execution
        """
        raise NotImplementedError

    @property
    def built( self ):
        """
        Returns True if all subvertices have been built.
        """
        return reduce( operator.and_,
                       map( lambda v : v.built, self.subvertices )
        )

    @built.setter
    def built( self, value ):
        if not value:
            for v in self.subvertices:
                v.built = False

    @property
    def loaded( self ):
        """
        Returns True if all subvertices have been loaded.
        """
        return reduce( operator.and_,
                       map( lambda v : v.loaded, self.subvertices )
        )

    @loaded.setter
    def loaded( self, value ):
        if not value:
            for v in self.subvertices:
                v.loaded = False
