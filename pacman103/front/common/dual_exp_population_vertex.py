'''
Created on 1 Apr 2014

@author: zzalsar4
'''
from pacman103.front.common.population_vertex import PopulationVertex, REGIONS

import math

NUM_SYNAPSE_PARAMS = 3 # tau_syn_E, tau_syn_E2 and tau_syn_I

class DualExponentialPopulationVertex(PopulationVertex):
    """
    This represents a population with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    
    def __init__( self, n_neurons, n_params, binary, constraints = None, 
            label = None, tau_syn_E = 5.0, tau_syn_E2 = 5.0, tau_syn_I = 5.0):
        
        # Instantiate the parent class
        super(DualExponentialPopulationVertex, self).__init__(
            n_neurons = n_neurons,
            n_params = n_params,
            binary = binary,
            constraints = constraints,
            label = label
        )
        self.tau_syn_E = tau_syn_E
        self.tau_syn_E2 = tau_syn_E2
        self.tau_syn_I = tau_syn_I
    
    def get_synapse_targets(self):
        """
        Gets the supported names of the synapse targets
        """
        return ("excitatory", "excitatory2", "inhibitory")
    
    def get_synapse_id(self, target_name):
        """
        Returns the numeric identifier of a synapse, given its name.  This
        is used by the neuron models.
        """
        if target_name == "excitatory":
            return 0
        elif target_name == "excitatory2":
            return 1
        elif target_name == "inhibitory":
            return 2
        return None
    
    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 2
    
    def getSynapseParameterSize(self, lo_atom, hi_atom):
        """
        Gets the size of the synapse parameters for a range of neurons
        """
        return NUM_SYNAPSE_PARAMS * 4 * ((hi_atom - lo_atom) + 1)
        
    def writeSynapseParameters(self, spec, machineTimeStep, subvertex ):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant for
        the exponential decay.
        
        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """
        
        # Set the focus to the memory region 3 (synapse parameters):
        spec.switchWriteFocus(region = REGIONS.SYNAPSE_PARAMS)
        spec.comment("\nWriting Synapse Parameters for %d Neurons:\n" % \
                                                         self.atoms)
        decay_ex = math.exp(-float(machineTimeStep) 
                / (1000.0 * float(self.tau_syn_E)))
        decay_ex2 = math.exp(-float(machineTimeStep) 
                / (1000.0 * float(self.tau_syn_E2)))
        decay_in = math.exp(-float(machineTimeStep) 
                / (1000.0 * float(self.tau_syn_I)))
        
        rescaled_decay_ex = int(decay_ex * pow(2, 32))
        rescaled_decay_ex2 = int(decay_ex2 * pow(2, 32))
        rescaled_decay_in = int(decay_in * pow(2, 32))
        
        spec.write(data=rescaled_decay_ex, repeats=subvertex.n_atoms)
        spec.write(data=rescaled_decay_ex2, repeats=subvertex.n_atoms)
        spec.write(data=rescaled_decay_in, repeats=subvertex.n_atoms)
        