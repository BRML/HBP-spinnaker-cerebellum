from pacman103.front.common.randomDistributions import generateParameter
from pacman103.front.pynn.connectors.abstract_connector import AbstractConnector
from pacman103.front.pynn.connectors.seed_info import SeedInfo
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.common.synapse_row_info import SynapseRowInfo

class FromListConnector( AbstractConnector ):
    """
    Make connections according to a list.

    :param `list` conn_list:
        a list of tuples, one tuple for each connection. Each
        tuple should contain::
        
         (pre_idx, post_idx, weight, delay)
         
        where pre_idx is the index (i.e. order in the Population,
        not the ID) of the presynaptic neuron, and post_idx is
        the index of the postsynaptic neuron.
    """

    def __init__(self, conn_list = [], safe = True, verbose = False ):
        """
        Creates a new FromListConnector.
        """
        self.conn_list = conn_list
        self.delay_so_far = 0
        self.weightSeeds = SeedInfo()
        self.delaySeeds  = SeedInfo()
        
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
        
        for i in range(0, len(self.conn_list)):
            conn = self.conn_list[i]
            pre_atom = generateParameter(conn[0], i)
            post_atom = generateParameter(conn[1], i)
            weight = generateParameter(conn[2], i)
            delay = generateParameter(conn[3], i) * delay_scale
            id_lists[pre_atom].append(post_atom)
            weight_lists[pre_atom].append(weight)
            delay_lists[pre_atom].append(delay)
            type_lists[pre_atom].append(synapse_type)
            
        connection_list = [SynapseRowInfo(id_lists[i], weight_lists[i], 
                    delay_lists[i], type_lists[i]) 
                for i in range(0, prevertex.atoms)]
        
        return SynapticList(connection_list)

