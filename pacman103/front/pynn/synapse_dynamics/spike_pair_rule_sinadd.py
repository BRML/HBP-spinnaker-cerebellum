'''
Created on 7 Apr 2014

@author: zzalsar4
'''
import math
import IPython
import logging
logger = logging.getLogger(__name__)

# Constants
# **NOTE** these should be passed through magical per-vertex build setting thing
LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 16
LOOKUP_TAU_MINUS_SHIFT = 0

# How many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 128

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# How large are the pre_synaptic_trace_entry_t structures
ALL_TO_ALL_EVENT_BYTES = 2
NEAREST_PAIR_EVENT_BYTES = 0

# Calculate number of words required for header
ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = 1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + ALL_TO_ALL_EVENT_BYTES)) / 4)
NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS = 1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + NEAREST_PAIR_EVENT_BYTES)) / 4)

class SpikePairRuleSinAdd(object):
    """
    Jesus Garrido's SinAdditive learning rule workalike. HWHM = 0.26* tau
    """
    def __init__(self, tau_plus = 20.0, tau_minus = 20.0, nearest = False, delay = 12):
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        self.nearest = nearest
        self.offset = -1.
        self.delay = delay
        self.custom_max_atoms_per_core = 20
        
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SpikePairRuleSinAdd)):
            return False
        return ((self.tau_plus == other.tau_plus) 
                and (self.tau_minus == other.tau_minus)
                and (self.nearest == other.nearest))

    def get_synaptic_row_header_words(self):
        return NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS if self.nearest else ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS
    
    def get_params_size_bytes(self):
        # we overestimate by a factor of 10 to accomodate for large LUTs due to machinetimestep
        # TODO: make that flexible, adapt to actual machinetimestep!
        return 20 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE) + 4 # for delay

        
    def get_vertex_executable_suffix(self):
        pre = 'sinexp_trace_'
        return pre+"nearest_pair" if self.nearest else pre+"pair"
        
    def write_plastic_params(self, spec, machineTimeStep, subvertex, 
            weight_scale):
        # adjust sizes to timestep
        lookup_plus_size = int(LOOKUP_TAU_PLUS_SIZE * 1000 / machineTimeStep)
        lookup_minus_size = int(LOOKUP_TAU_MINUS_SIZE * 1000 / machineTimeStep)
        lookup_plus_shift = int(LOOKUP_TAU_PLUS_SHIFT * 1000 / machineTimeStep)
        lookup_minus_shift = int(LOOKUP_TAU_MINUS_SHIFT * 1000 / machineTimeStep)
            
#            raise NotImplementedError("STDP LUT generation currently only supports 1ms timesteps")
# so we should scale tau_* by machineTimeStep!
        
        # Write lookup tables
        
        timeConstantReciprocal = 1. / float(self.tau_plus) / ( 1000. / machineTimeStep )    # increase resolution by 8x
        zeroindex = self.offset/timeConstantReciprocal
        shiftedzeroindex = self.delay * 1000./machineTimeStep + zeroindex
        # write delay to spec
        spec.write(data=int(shiftedzeroindex), sizeof="uint32") # check scaling to machineTimeStep
        
        times,dws = self.__write_sinexp_decay_lut(spec, timeConstantReciprocal, lookup_plus_size, lookup_plus_shift)
        
        self.__write_sinexp_decay_lut(spec, self.tau_minus, lookup_minus_size, lookup_minus_shift) # one too many!
#        logger.warning("SINEXP-LUT written, zerooffset = %d",shiftedzeroindex)
        #IPython.embed() 
    
    # Move somewhere more generic STDPRuleBase perhaps?
    def __write_sinexp_decay_lut(self, spec, timeConstantReciprocal, size, shift):
        offset = self.offset

        # Check that the last 
        lastTime = (size - 1) << shift
        lastValue = float(lastTime) * timeConstantReciprocal + offset
        lastExponentialFloat = math.exp(-lastValue)*math.cos(lastValue)**20 
        if spec.doubleToS511(lastExponentialFloat) != 0:
            logger.warning("STDP lookup table with size %u is too short to contain decay with time constant %u - last entry is %f" % (size, 1./timeConstantReciprocal, lastExponentialFloat))

        times = []
        dws = []
        # Generate LUT
        for i in range(size):
            # Apply shift to get time from index 
            time = (i << shift)

            # Multiply by time constant and calculate negative exponential
            value = float(time) * timeConstantReciprocal + offset
            exponentialFloat = math.exp(-value)*math.cos(value)**20

            # Convert to fixed-point and write to spec
            spec.write(data=spec.doubleToS511(exponentialFloat), sizeof="s511")
            times.append(value)
            dws.append(exponentialFloat)
        return times,dws
           
