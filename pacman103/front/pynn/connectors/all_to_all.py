from pacman103.front.common.randomDistributions import generateParameter, generateParameterArray
from pacman103.front.common.synapse_row_info import SynapseRowInfo
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.pynn.connectors.abstract_connector import AbstractConnector

import numpy

class AllToAllConnector( AbstractConnector ):
    """
    Connects all cells in the presynaptic population to all cells in the 
    postsynaptic population.

    :param `bool` allow_self_connections: 
        if the connector is used to connect a
        Population to itself, this flag determines whether a neuron is
        allowed to connect to itself, or only to other neurons in the
        Population.
    :param `float` weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param `float` delays:  -- as `weights`. If `None`, all synaptic delays will 
        be set to the global minimum delay.
    :param `pyNN.Space` space: 
        a Space object, needed if you wish to specify distance-
        dependent weights or delays - not implemented
        
    """
    def __init__( self, weights = 0.0, delays = 1,
                  allow_self_connections = True ):
        """
        Creates a new AllToAllConnector.
        """
        self.weights = weights
        self.delays = delays
        self.allow_self_connections = allow_self_connections
        
    def generate_synapse_list(self, prevertex, postvertex, delay_scale, 
            synapse_type):
        
        connection_list = list()
        for _ in range(0, prevertex.atoms):
            present = numpy.ones(postvertex.atoms, 
                    dtype=numpy.uint32)
            n_present = postvertex.atoms
            
            ids = numpy.where(present)[0]
            delays = (generateParameterArray(self.delays, n_present, present)
                    * delay_scale)
            weights = generateParameterArray(self.weights, n_present, present)
            synapse_types = (numpy.ones(len(ids), dtype='uint32') 
                    * synapse_type)
            
            connection_list.append(SynapseRowInfo(ids, weights, delays,
                    synapse_types))
                    
        return SynapticList(connection_list)
