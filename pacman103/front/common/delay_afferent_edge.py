from pacman103.lib.graph import Edge

class DelayAfferentEdge(Edge):
    
    def __init__(self, prevertex, delayvertex, constraints=None, label=None):
        super(DelayAfferentEdge, self).__init__(prevertex, delayvertex, 
                constraints=constraints, label=label)
    
    def filterSubEdge(self, subedge):
        """
        Filters a subedge of this edge if the edge is not a one-to-one edge
        """
        if ((subedge.presubvertex.lo_atom != subedge.postsubvertex.lo_atom) or
             (subedge.presubvertex.hi_atom != subedge.postsubvertex.hi_atom)):
            return True
        
        return False
