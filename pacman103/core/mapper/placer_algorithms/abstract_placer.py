__author__ = 'stokesa6'

class AbstractPlacer(object):
    
    def __init__(self, dao):
        """
        Sets up any internal parameters in the placer
        :param dao: The dao to use
        """
        raise NotImplementedError

    def place_all(self):
        """
        Places all of the subvertices from the dao, 
        and stores the placements back in that dao
        """
        raise NotImplementedError
    
    def get_maximum_resources(self, constraints):
        """
        Gets a set of maximum resources that can be assigned to any 
        single subvertex
        :param constraints: A set of constraints that limit where the resources
            are obtained from on a machine
        :return: A lib_map.Resources object containing the resources available,
            or None if some resources are exhausted within the constraints
        """
        raise NotImplementedError

    def place_subvertex(self, resources, constraints):
        """
        Places a subvertex, with a set of requirements for the subvertex
        :param resources: The resources required by the subvertex.  This must
            be less than or equal to the resources returned by 
            get_maximum_resources
        :return: x, y, p coordinates where the resources were placed
        """
        raise NotImplementedError
    
    def unplace_subvertex(self, processor, resources):
        """
        Reverses the placement of a vertex
        """
        raise NotImplementedError
    
    def place_virtual_subvertex(self, constraints, n_virtual_cores):
        """
        Places a virtual vertex
        """
        raise NotImplementedError
