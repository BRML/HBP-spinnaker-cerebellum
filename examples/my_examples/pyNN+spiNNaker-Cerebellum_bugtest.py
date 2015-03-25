import IPython
import time
from numpy import arange,ones_like,repeat
sim = "spiNNaker"
exec("import pyNN." + sim + " as p")
from pacman103.front.common.external_device import ExternalDevice
#from PynnSpinnIO import *
spIOedge = 3 # 3 for spiNN-3, 4 for spiNN-4,5
timestep = 0.6
runtime=48*60*60e3

spin_control = p.setup(timestep = timestep, min_delay = timestep, max_delay = 4.0, threads=4)

# set maximum number of standard LIF-cells per core 
# assuming 256 is fine at timestep=1.0 and scales linearly 
maxif1 = 200 #256
maxif = int(maxif1 * (timestep*1e3))
p.set_number_of_neurons_per_core("IF_cond_exp",maxif)

size_pc = 8 # separate set (size 16) for left and right
size_dcn = size_pc/2

weights_pcdcn = 0.001 # values above ~0.002 cause spikes in the DCNs !!



# input layers

max_inp_rate = 30

# 'listen_key': 0xFEFFFE30 for left error
#iosourceR_params = {'min_rate': 0.05, 'max_rate': 100, 'src_type': 'glob_pois', 'sensormax': 500, 'sensormin': 0, 'listen_key': 0xFEFFFE31}
#inp_iolayer_right = p.Population(size_io, p.SpikeSourceRemote, iosourceR_params , label = "ioR_PLOT")
#inp_iolayer_right.set_mapping_constraint({'y': 0, 'x': 0})
#inp_iolayer_right.stream()


# neuron layers

pop_pclayer_left = p.Population(size_pc, p.SpikeSourcePoisson, {'rate' : 100, 'start' : 0, 'duration' : 10e9}, label = "pcL_PLOT")
pop_pclayer_left.stream()

cellparams_dcnlayer = {
 'tau_refrac' : 1.29099444874,
 'tau_m' : 12.9099444874,
 'e_rev_E' : 0.0,
 'cm' : 0.00258198889747,
 'e_rev_I' : -80.0,
 'v_thresh' : -40.0,
 'tau_syn_E' : 0.645497224368,
 'v_rest' : -70.0,
 'tau_syn_I' : 12.9099444874,
 'v_reset' : -70.0,
 }

pop_dcnlayer_left = p.Population(size = size_dcn, cellclass = p.IF_cond_exp, cellparams = cellparams_dcnlayer, label = "dcnL_PLOT")
pop_dcnlayer_left.stream()

# we connect a set of pc cells (usually 2) to a single dcn cell
rep = size_pc/size_dcn # should be 2, such that 2 pc are mapped to 1 dcn
target_list = repeat(range(size_dcn),rep).tolist()
source_list = range(size_pc)
pro_pcdcnsynapsis_connlist = zip(source_list,target_list,[weights_pcdcn]*size_pc,[1.0]*size_pc)
pro_pcdcnsynapsis_connector_left = p.FromListConnector(pro_pcdcnsynapsis_connlist)

pro_pcdcnsynapsis_left = p.Projection(pop_pclayer_left, pop_dcnlayer_left, pro_pcdcnsynapsis_connector_left, target = "inhibitory" , synapse_dynamics = None, label = "pcdcnsynapsis_left")

# run the simulation, we made this a 2 step process
# first set up and upload everything
p.run(runtime, do_load = True, do_run = False)
# then start!
spin_control.run(spin_control.dao.app_id)
p.end()

