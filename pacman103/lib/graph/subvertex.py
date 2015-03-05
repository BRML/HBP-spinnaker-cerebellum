from pacman103.lib import lib_map

class Subvertex( object ):
    """
    Represents a subvertex, that is, a subset of the atoms in a vertex following
    the partitioning stage.

    *Side effects*:
        Upon instantiation, the parent vertex is updated to include a reference
        to the instance.

    :param `pacman103.lib.graph.Vertex` vertex: parent vertex.
    :param int lo_atom: lowest ID of the vertex atoms in the subvertex.
    :param int hi_atom: highest ID of the vertex atoms in the subvertex.
    """

    def __init__(self, vertex, lo_atom, hi_atom, resources):
        # Record passed parameters
        self.vertex = vertex
        self.lo_atom = lo_atom
        self.hi_atom = hi_atom
        self.resources = resources

        # Set up reference to placement and lists of subedges
        self.in_subedges = list()
        self.out_subedges = list()
        self.placement = None

        # Record self in parent
        self.vertex.subvertices.append(self)

        # Built and loaded
        self._built = self._loaded = False
        
    def get_resources(self):
        return self.resources

    def generateDataSpec( self, processor, dao ):
        """
        Call the parent vertex to generate the data spec for this subvertex.
        """
        return self.vertex.generateDataSpec( processor, self, dao )

    @property
    def n_atoms( self ):
        """The number of neurons for this subvertex."""
        return self.hi_atom - self.lo_atom + 1
    
    def __getstate__(self):
        return {"lo_atom": self.lo_atom,
                "hi_atom": self.hi_atom}
        
    def __setstate__(self, state):
        self.lo_atom = state["lo_atom"]
        self.hi_atom = state["hi_atom"]

    @property
    def loaded( self ):
        return self._loaded

    @loaded.setter
    def loaded( self, value ):
        self._loaded = value

    @property
    def built( self ):
        return self._built

    @built.setter
    def built( self, value ):
        self._built = value
