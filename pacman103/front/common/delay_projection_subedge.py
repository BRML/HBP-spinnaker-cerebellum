from pacman103.front.common.projection_subedge import ProjectionSubedge 
from pacman103.front.common.synaptic_list import SynapticList
from pacman103.front.common.synapse_row_info import SynapseRowInfo

import logging
logger = logging.getLogger(__name__)

class DelayProjectionSubedge(ProjectionSubedge):
    
    def __init__(self, edge, presubvertex, postsubvertex):
        super(DelayProjectionSubedge, self).__init__(edge, presubvertex, 
                postsubvertex)
        
        self.synapse_sublist = None
        self.synapse_delay_rows = None
    
    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self.synapse_sublist is None:
            
            synapse_sublist = self.edge.synapse_list.create_atom_sublist(
                    self.presubvertex.lo_atom, self.presubvertex.hi_atom,
                    self.postsubvertex.lo_atom, self.postsubvertex.hi_atom)
            
#             if logger.isEnabledFor("debug"):
#                 logger.debug("Original Synapse List rows:")
#                 orig_list = synapse_sublist.get_rows()
#                 for i in range(len(orig_list)):
#                     logger.debug("{}: {}".format(i, orig_list[i]))
        
            if synapse_sublist.get_n_rows() > 256:
                raise Exception(
                        "Delay sub-vertices can only support up to" 
                        + " 256 incoming neurons!")
                
            full_delay_list = list()
            for i in range(0, self.edge.num_delay_stages):
                min_delay = (i * self.edge.max_delay_per_neuron)
                max_delay = min_delay + self.edge.max_delay_per_neuron
                delay_list = synapse_sublist.get_delay_sublist(min_delay, 
                        max_delay)
                
#                 if logger.isEnabledFor("debug"):
#                     logger.debug("    Rows for delays {} - {}:".format(
#                             min_delay, max_delay))
#                     for i in range(len(delay_list)):
#                         logger.debug("{}: {}".format(i, delay_list[i]))
                
                full_delay_list.extend(delay_list)
                
                # Add extra rows for the "missing" items, up to 256
                if (i + 1) < self.edge.num_delay_stages:
                    for _ in range(0, 256 - len(delay_list)):
                        full_delay_list.append(SynapseRowInfo([], [], [], []))
            self.synapse_sublist = SynapticList(full_delay_list)
            self.synapse_delay_rows = len(full_delay_list)
        return self.synapse_sublist
    
    def get_synaptic_data(self, controller, delay_offset):
        delay_list = self.postsubvertex.vertex.get_synaptic_data(controller, 
                self.presubvertex, self.synapse_delay_rows, self.postsubvertex, 
                self.edge.synapse_row_io).get_rows()
        rows = list()
        for pre_atom in range(0, self.presubvertex.n_atoms):
            rows.append(SynapseRowInfo([], [], [], []))
        
        for i in range(0, self.edge.num_delay_stages):
            min_delay = (i * self.edge.max_delay_per_neuron) + delay_offset
            list_offset = i * 256
            for pre_atom in range(0, self.presubvertex.n_atoms):
                row = delay_list[list_offset + pre_atom]
                rows[pre_atom].append(row, min_delay=min_delay)
        return SynapticList(rows)
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self.synapse_sublist = None
