class Subedge( object ):
    """
    Represents a subedge, that is, an edge between two subvertices.

    *Side effects*:
        Upon instantiation, the parent edge and the pre- and post-subvertices
        are updated to include a reference to the instance.

    :param `pacman103.lib.graph.Edge` edge: parent edge.
    :param `pacman103.lib.graph.Subvertex` presubvertex: source subvertex.
    :param `pacman103.lib.graph.Subvertex` postsubvertex:
        destination subvertex.
    """

    def __init__(self, edge, presubvertex, postsubvertex):
        # Record passed parameters
        self.edge = edge
        self.pruneable = False
        self.presubvertex = presubvertex
        self.postsubvertex = postsubvertex

        # Record self in parent and in pre- and post-subvertices
        self.edge.subedges.append(self)
        self.presubvertex.out_subedges.append(self)
        self.postsubvertex.in_subedges.append(self)

        #holders for routing keys data
        self.key = None
        self.mask = None
        self.key_mask_combo = None
        self.routing = None
