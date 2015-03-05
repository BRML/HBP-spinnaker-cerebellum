from pacman103.front.common.randomDistributions import generateParameter
from pacman103.front.pynn.connectors.abstract_connector import AbstractConnector
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.common.synapse_row_info import SynapseRowInfo

class OneToOneConnector( AbstractConnector ):
    """
    Where the pre- and postsynaptic populations have the same size, connect 
    cell i in the presynaptic population to cell i in the postsynaptic 
    population for all i.

    :param weights:
        may either be a float, a !RandomDistribution object, a list/
        1D array with at least as many items as connections to be
        created. Units nA.
    :param delays:
        as `weights`. If `None`, all synaptic delays will be set
        to the global minimum delay.
         
    """
    def __init__( self, weights = 0.0, delays = 1 ):
        """
        Creates a new connector.
        """
        self.weights = weights
        self.delays = delays
        
    def generate_synapse_list(self, prevertex, postvertex, delay_scale,
            synapse_type):
        connection_list = list()
        for pre_atom in range(0, prevertex.atoms):
            delay   = generateParameter(self.delays, pre_atom) * delay_scale
            weight  = generateParameter(self.weights, pre_atom)
            connection_list.append(SynapseRowInfo([pre_atom], [weight],
                     [delay], [synapse_type]))
                    
        return SynapticList(connection_list)
