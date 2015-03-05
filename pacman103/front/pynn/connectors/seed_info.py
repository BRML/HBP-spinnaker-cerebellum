
class SeedInfo( object ):
    """
    Parent seed for random numbers plus a dictionary of seeds at various
    intervals so the same stream of random numbers can be re-generated later.
    """
    def __init__( self):
        self.parent_seed = 0
        self.seed_stream = dict()
        self.seed_stream_indices = list()
    
    
