from pacman103.front.common.randomDistributions import generateParameterArray
from pacman103.front.pynn.connectors.abstract_connector import AbstractConnector
from pacman103.front.common.synapse_row_info import SynapseRowInfo
from pacman103.front.common.synaptic_list import SynapticList

import numpy

class FixedProbabilityConnector( AbstractConnector ):
    """
    For each pair of pre-post cells, the connection probability is constant.

    :param `float` p_connect:
        a float between zero and one. Each potential connection
        is created with this probability.
    :param `bool` allow_self_connections:
        if the connector is used to connect a
        Population to itself, this flag determines whether a neuron is
        allowed to connect to itself, or only to other neurons in the
        Population.
    :param weights: 
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays: 
        If `None`, all synaptic delays will be set
        to the global minimum delay.
    :param `pyNN.Space` space: 
        a Space object, needed if you wish to specify distance-
        dependent weights or delays - not implemented
    """
    def __init__(self, p_connect, weights = 0.0, delays = 1,
                  allow_self_connections = True):
        """
        Creates a new FixedProbabilityConnector.
        """
        self.p_connect = p_connect
        self.weights = weights
        self.delays = delays
        self.allow_self_connections = allow_self_connections
        
    def generate_synapse_list(self, prevertex, postvertex, delay_scale,
            synapse_type):
        rows = list()
        for _ in range(0, prevertex.atoms):
            
            present = numpy.random.rand(postvertex.atoms) <= self.p_connect
            n_present = numpy.sum(present)
            
            ids = numpy.where(present)[0]
            delays = (generateParameterArray(self.delays, n_present, present)
                    * delay_scale)
            weights = generateParameterArray(self.weights, n_present, present)
            synapse_types = (numpy.ones(len(ids), dtype='uint32') 
                    * synapse_type)
            
            rows.append(SynapseRowInfo(ids, weights, delays, synapse_types))
        return SynapticList(rows)
