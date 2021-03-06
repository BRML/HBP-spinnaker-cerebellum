from pacman103.front.common.randomDistributions import generateParameter
from pacman103.front.pynn.connectors.abstract_connector import AbstractConnector
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.common.synapse_row_info import SynapseRowInfo
import random

class MultapseConnector( AbstractConnector ):
    """
    Create a multapse connector. The size of the source and destination 
    populations are obtained when the projection is connected. The number of 
    synapses is specified. when instantiated, the required number of synapses
    is created by selecting at random from the source and target populations 
    with replacement. Uniform selection probability is assumed.

    : param numSynapses:
        Integer. This is the total number of synapses in the connection.
    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        as `weights`. If `None`, all synaptic delays will be set
        to the global minimum delay.
         
    """
    def __init__( self, numSynapses = 0, weights = 0.0, delays = 1,
            connectionArray = None ):
        """
        Creates a new connector.
        """
        self.numSynapses = numSynapses
        self.weights = weights
        self.delays = delays
        self.connectionArray = connectionArray
        
    def generate_synapse_list(self, prevertex, postvertex, delay_scale,
            synapse_type):
        id_lists = list()
        weight_lists = list()
        delay_lists = list()
        type_lists = list()
        for _ in range(0, prevertex.atoms):
            id_lists.append(list())
            weight_lists.append(list())
            delay_lists.append(list())
            type_lists.append(list())
            
        numIncomingAxons = prevertex.atoms
        numTargetNeurons = postvertex.atoms
        
        for _ in range(0, self.numSynapses):
            source = int(random() * numIncomingAxons)
            target = int(random() * numTargetNeurons)
            weight = generateParameter(self.weights, target)
            delay = generateParameter(self.weights, target) * delay_scale
            id_lists[source].append(target)
            weight_lists[source].append(weight)
            delay_lists[source].append(delay)
            type_lists[source].append(synapse_type)
            
        connection_list = [SynapseRowInfo(id_lists[i], weight_lists[i], 
                    delay_lists[i], type_lists[i]) 
                for i in range(0, prevertex.atoms)]
        
        return SynapticList(connection_list)
