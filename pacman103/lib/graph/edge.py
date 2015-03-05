from pacman103.lib import lib_map
from pacman103.lib.graph.subedge import Subedge

class Edge( object ):
    """
    Represents an edge between two vertices of the input graph.

    *Side effects*:
        On instantiation, the pre- and post-vertices are updated to include a
        reference to the instance.

    :param `pacman103.lib.graph.Vertex` prevertex: source vertex.
    :param `pacman103.lib.graph.Vertex` postvertex: destination vertex.
    :param `pacman103.lib.lib_map.EdgeConstraints` constraints:
        [To be determined.]
    """

    def __init__( self, prevertex, postvertex, constraints=None,
                  label=None):
        # Record passed parameters
        self.prevertex  = prevertex
        self.postvertex = postvertex
        self.label      = label

        if constraints is None: self.constraints = lib_map.EdgeConstraints()
        else:                   self.constraints = constraints

        # Set up reference list to subedges
        self.subedges = list()

        # Record self in pre- and post-vertices
        self.prevertex.out_edges.append(self)
        self.postvertex.in_edges.append(self)
        
    def create_subedge(self, presubvertex, postsubvertex):
        """
        Create a subedge between presubvertex and postsubvertex
        """
        return Subedge(self, presubvertex, postsubvertex)

    def filterSubEdge(self, subedge):
        """
        Method is called to allow a given sub-edge of this edge to prune 
        itself if it serves no purpose. This generic method does nothing
        and must be overridden in derived classes.
        """
        return False

