class VertexModel:
    """
    Superclass for all vertex models. Subclasses of this class should be static,
    that is, intented to provide static functions and not to be instantiated.
    """

    def __init__(self):
        raise Exception("TODO description string") #to the effect that this class should not be instantiated


    @staticmethod
    def build_load_targets(subvertex):
        """
        Build the data structures for this subvertex of this model.
        """
        raise NotImplementedError("TODO description string")


    @staticmethod
    def generate_routing_info(subedge): #TODO this needs to take the DAO as a parameter
        """
        Generate the routing key and mask for this subedge of this model.
        """
        raise NotImplementedError("TODO description string")


    @staticmethod
    def get_requirements_per_atom():
        """
        Get the resource requirements per atom of this model.
        """
        raise NotImplementedError("TODO description string")



class EdgeModel:
    """
    Superclass for all edge models. Subclasses of this class should be static,
    that is, intented to provide static functions and not to be instantiated.
    """
    pass
