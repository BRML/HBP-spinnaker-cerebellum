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
size_io = size_pc
size_dcn = size_pc/2

weights_mfdcn = 0.003 # 0.005
weights_pcdcn = 0.002 # was 0.08; values above ~0.002 cause spikes in the DCNs !! this is a bug most likely caused by membrane potential overflow ...
weight_mfgrc = 0.0022 # will be like the cummulative weight -> scaled by mf dimension
# we might want different weights for different input later on!
#weights_dcndcn = 0.001 # test!

# input layers

max_inp_rate = 30
# input layers
inp_mflayer_left = []
mflayer0_current_params = {'sensormin': 1248, 'sensormax': 2848, 'max_rate': max_inp_rate, 'min_rate': 0.1, 'listen_key': 0xFEFFFE20, 'src_type': 'rbf_det', 'gauss_width': 1.0} # before: 1148 - 2948
mflayer0_current = p.Population(16, p.SpikeSourceRemote, mflayer0_current_params, label = "mf_curr_pos_PLOT")
inp_mflayer_left.append(mflayer0_current)

mflayer0_currset_params = {'sensormin': 0.0, 'sensormax': 1600.0, 'max_rate': max_inp_rate, 'min_rate': 0.1, 'listen_key': 0xFEFFFE30, 'src_type': 'rbf_det', 'gauss_width': 1.0}
mflayer0_currset = p.Population(16, p.SpikeSourceRemote, mflayer0_currset_params, label = "mf_set_pos_PLOT")
inp_mflayer_left.append(mflayer0_currset)

#mflayer0_currvel_params = {'sensormin': 0.0, 'sensormax': 1000.0, 'max_rate': max_inp_rate, 'min_rate': 0.1, 'listen_key': 0xFEFFFE33, 'src_type': 'rbf_det', 'gauss_width': 0.5} # sensormax = 2 * max_ang_vel
#mflayer0_currvel = p.Population(4, p.SpikeSourceRemote, mflayer0_currvel_params, label = "mf_curr_vel_PLOT")
#inp_mflayer_left.append(mflayer0_currvel)

mflayer0_setvel_params = {'sensormin': 0.0, 'sensormax': 1000.0, 'max_rate': max_inp_rate, 'min_rate': 0.1, 'listen_key': 0xFEFFFE34, 'src_type': 'rbf_det', 'gauss_width': 0.5} # sensormax = 2 * max_ang_vel
mflayer0_setvel = p.Population(4, p.SpikeSourceRemote, mflayer0_setvel_params, label = "mf_set_vel_PLOT")
inp_mflayer_left.append(mflayer0_setvel)

# we have 16*16*4*2*8 input neurons = 16384 GrCs per muscle
# ( _sans current_: 8192 neurons )

for pop in inp_mflayer_left:
    pop.set_mapping_constraint({'y': 0, 'x': 0})
    pop.stream()

# 'listen_key': 0xFEFFFE30 for left error
iosourceR_params = {'min_rate': 0.05, 'max_rate': 120, 'src_type': 'glob_pois', 'sensormax': 500, 'sensormin': 0, 'listen_key': 0xFEFFFE31}
iosourceL_params = iosourceR_params.copy()
iosourceL_params["listen_key"] = 0xFEFFFE32
inp_iolayer_left = p.Population(size_io, p.SpikeSourceRemote, iosourceL_params , label = "io_L_PLOT")
inp_iolayer_right = p.Population(size_io, p.SpikeSourceRemote, iosourceR_params , label = "io_R_PLOT")
inp_iolayer_right.set_mapping_constraint({'y': 0, 'x': 0})
inp_iolayer_left.set_mapping_constraint({'y': 0, 'x': 0})
inp_iolayer_right.stream()
inp_iolayer_left.stream()

# neuron layers

cellparams_pclayer = {
 'tau_refrac' : 2.58198889747,
 'tau_m' : 40.343576523,
 'e_rev_E' : 0.0,
 'cm' : 0.645497224368,
 'e_rev_I' : -80.0,
 'v_thresh' : -52.0,
 'tau_syn_E' : 1.54919333848,
 'v_rest' : -70.0,
 'tau_syn_I' : 12.0062483732,
 'v_reset' : -70.0,
 }
pop_pclayer_left= p.Population(size = size_pc, cellclass = p.IF_cond_exp, cellparams = cellparams_pclayer, label = "pc_L_PLOT")
pop_pclayer_right= p.Population(size = size_pc, cellclass = p.IF_cond_exp, cellparams = cellparams_pclayer, label = "pc_R_PLOT")
pops_pclayer = [pop_pclayer_left,pop_pclayer_right]
for pop in pops_pclayer:
    pop.stream()
#pop_pclayer.record()

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

pop_dcnlayer_left = p.Population(size = size_dcn, cellclass = p.IF_cond_exp, cellparams = cellparams_dcnlayer, label = "dcn_L_PLOT")
pop_dcnlayer_right = p.Population(size = size_dcn, cellclass = p.IF_cond_exp, cellparams = cellparams_dcnlayer, label = "dcn_R_PLOT")
pops_dcnlayer = [pop_dcnlayer_left, pop_dcnlayer_right]

pops_myomotor = []
myomotorR_params = { 'virtual_chip_coords': {'y': 254, 'x': 254}, 
                    'decay_factor': 0.960, #.965
                    'connected_chip_edge': spIOedge, 
                    'sample_time': 25.0, # 40
                    'output_scale': 9.0, # 2.2
                    'monitorID': 0x120, 
                    'motorID': 0x110, 
                    'kernel_amplitude': 1.28, #for sample_time 40: 0.8 #0.894427191, # 0.4472135954999579
                    'threshold': 130, # 120, 40
                    'connected_chip_coords': {'y': 0, 'x': 0}
                  }
myomotorL_params = myomotorR_params.copy()
myomotorL_params["monitorID"] = 0x125
myomotorL_params["motorID"] = 0x115

myomotor_left = p.Population(size_dcn, p.MyoRobotMotorControl, myomotorL_params , label = "myolayerL")
myomotor_right = p.Population(size_dcn, p.MyoRobotMotorControl, myomotorR_params , label = "myolayerR")
pops_myomotor = [myomotor_left, myomotor_right]
# we have different dcnlayers for left, right
for pop in pops_myomotor:
    pop.set_mapping_constraint({'y': 0, 'x': 0})

# no added signal, ATM.
#myoexc_source_params = {'min_rate': 0.05, 'max_rate': 100, 'src_type': 'glob_det', 'sensormax': 4000, 'sensormin': 0, 'listen_key': 0xFEFFFE40}
#inp_myoexc_left = p.Population(size_dcn, p.SpikeSourceRemote, myoexc_source_params.copy() , label = "myoexc_right")
#inp_myoexc_left.set_mapping_constraint({'y': 0, 'x': 0})
#inp_myoexc_left.stream()
#proj_myoexc_left = p.Projection(inp_myoexc_left, myomotor_left, p.OneToOneConnector(weights=1.0,delays=1.0))
#inp_myoexc_right.stream()

cellparams_grclayer = {
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

grcsize_left = 1
# how many GrCs do we really need?
for pop in inp_mflayer_left:
    grcsize_left *= pop.size
pop_grclayer_left = p.Population(size = grcsize_left, cellclass = p.IF_cond_exp, cellparams = cellparams_grclayer, label = "grc") #_PLOT
pop_grclayer_left.stream() # to be tested for performance!

#weight_mfgrc = 0.5 # will be like the cummulative weight -> scaled by mf dimension
# we might want different weights for different input later on!
out_list = arange(0, grcsize_left)
projs_mfgrc_left = []
dimsize = 1
scweight_mfgrc = weight_mfgrc
for inpop in inp_mflayer_left:
    in_list = (out_list / dimsize) % inpop.size
    dimsize *= inpop.size
    weights_list = scweight_mfgrc * ones_like(out_list) # will randomize at some point
    delays_list = ones_like(out_list)
    connlist = zip(in_list, out_list, weights_list, delays_list)
    projs_mfgrc_left.append(p.Projection(inpop, pop_grclayer_left, p.FromListConnector(connlist)))

#grcsize_right = 1
# how many GrCs do we really need?
#for pop in inp_mflayer_right:
#    grcsize_right *= pop.size
#pop_grclayer_right = p.Population(size = grcsize_right, cellclass = p.IF_cond_exp, cellparams = cellparams_grclayer, label = "grclayerR_PLOT") #_PLOT
#pop_grclayer_right.stream()

#weight_mfgrc = 0.5 # will be like the cummulative weight -> scaled by mf dimension
# we might want different weights for different input later on!
#out_list = arange(0, grcsize_right)
#projs_mfgrc_right = []
#dimsize = 1
#scweight_mfgrc = weight_mfgrc / len(inp_mflayer_right)
#for inpop in inp_mflayer_left:
#    in_list = (out_list / dimsize) % inpop.size
#    dimsize *= inpop.size
#    weights_list = scweight_mfgrc * ones_like(out_list) # will randomize at some point
#    delays_list = ones_like(out_list)
#    connlist = zip(in_list, out_list, weights_list, delays_list)
#    projs_mfgrc_right.append(p.Projection(inpop, pop_grclayer_right, p.FromListConnector(connlist)))


pops_grclayer = [pop_grclayer_left]

for dcn,myo in zip(pops_dcnlayer,pops_myomotor):
    p.Projection(dcn, myo, p.OneToOneConnector(weights=1.0,delays=1.0))
    dcn.stream()

# synapse layers
wdep_grcpcsynapsis = p.AdditiveWeightDependence(w_min = 0.0, w_max = 0.4, A_plus = 0.0015, A_minus = 0.0020) # w_max = 0.4, A_plus = 0.0015, A_minus = 0.0018
tdep_grcpcsynapsis = p.SpikePairRuleSinAdd(tau_minus = 50., tau_plus = 50., delay = 100.0, nearest = False ) # delay 70-100
stdp_grcpcsynapsis = p.STDPMechanism(timing_dependence = tdep_grcpcsynapsis, weight_dependence = wdep_grcpcsynapsis, voltage_dependence = None )
syndyn_grcpcsynapsis = p.SynapseDynamics( slow = stdp_grcpcsynapsis)

rng = p.NumpyRNG(seed=hash(time.time()))
grcpc_weights_distribution = p.RandomDistribution('uniform',[0.05,0.09],rng)
pro_grcpcsynapsis_connector = p.FixedProbabilityConnector(0.8,weights=grcpc_weights_distribution)
pro_grcpcsynapsis_left = p.Projection(pop_grclayer_left, pop_pclayer_left, pro_grcpcsynapsis_connector, target = "excitatory" , synapse_dynamics = syndyn_grcpcsynapsis, label = "grcpcsynapsis")
pro_grcpcsynapsis_right = p.Projection(pop_grclayer_left, pop_pclayer_right, pro_grcpcsynapsis_connector, target = "excitatory" , synapse_dynamics = syndyn_grcpcsynapsis, label = "grcpcsynapsis")
pro_grcpcsynapses = [pro_grcpcsynapsis_left, pro_grcpcsynapsis_right]

# limit number of neurons per core based on the number of dentritic inputs we receive
for proj in pro_grcpcsynapses:
    proj.projection_edge.postvertex.custom_max_atoms_per_core = max(1,2000 / proj.projection_edge.prevertex.atoms)

pro_iopcsynapsis_connector = p.OneToOneConnector(weights=0.0,delays=1.0)
pro_iopcsynapsis_left = p.Projection(inp_iolayer_left, pop_pclayer_left, pro_iopcsynapsis_connector, target = "inhibitory" , synapse_dynamics = None, label = "iopcsynapsis_left")
pro_iopcsynapsis_right = p.Projection(inp_iolayer_right, pop_pclayer_right, pro_iopcsynapsis_connector, target = "inhibitory" , synapse_dynamics = None, label = "iopcsynapsis_right")

# connect all inputs in inp_mflayer to their respective dcn
pro_mfdcnsynapsis_connector = p.AllToAllConnector(weights=weights_mfdcn,delays=1.0)
for i, inp in enumerate(inp_mflayer_left):
	pro_mfdcnsynapsis_left = p.Projection(inp, pop_dcnlayer_left, pro_mfdcnsynapsis_connector, target = "excitatory" , synapse_dynamics = None, label = "mfdcnsynapsis_left")
	pro_mfdcnsynapsis_right = p.Projection(inp, pop_dcnlayer_right, pro_mfdcnsynapsis_connector, target = "excitatory" , synapse_dynamics = None, label = "mfdcnsynapsis_right")

# we connect a set of pc cells (usually 2) to a single dcn cell
rep = size_pc/size_dcn # should be 2, such that 2 pc are mapped to 1 dcn
target_list = repeat(range(size_dcn),rep).tolist()
source_list = range(size_pc)
pro_pcdcnsynapsis_connlist = zip(source_list,target_list,[weights_pcdcn]*size_pc,[1.0]*size_pc)
pro_pcdcnsynapsis_connector_left = p.FromListConnector(pro_pcdcnsynapsis_connlist)

pro_pcdcnsynapsis_left = p.Projection(pop_pclayer_left, pop_dcnlayer_left, pro_pcdcnsynapsis_connector_left, target = "inhibitory" , synapse_dynamics = None, label = "pcdcnsynapsis_left")
pro_pcdcnsynapsis_right = p.Projection(pop_pclayer_right, pop_dcnlayer_right, pro_pcdcnsynapsis_connector_left, target = "inhibitory" , synapse_dynamics = None, label = "pcdcnsynapsis_right")

# test inhibitory connections between both DCNs
#pro_dcndcnsynapsis_connector = p.AllToAllConnector(weights=weights_dcndcn,delays=1.0)
#pro_dcnlrsynapsis = p.Projection(pop_dcnlayer_left, pop_dcnlayer_right, pro_dcndcnsynapsis_connector, target = "inhibitory" , synapse_dynamics = None, label = "dcnlrsynapsis")
#pro_dcnrlsynapsis = p.Projection(pop_dcnlayer_right, pop_dcnlayer_left, pro_dcndcnsynapsis_connector, target = "inhibitory" , synapse_dynamics = None, label = "dcnrlsynapsis")

# run the simulation, we made this a 2 step process
# first set up and upload everything
p.run(runtime, do_load = True, do_run = False)
# then start!
spin_control.run(spin_control.dao.app_id)
#grclayerSpikes = pop_grclayer.getSpikes(compatible_output = True)
#grclayerSpikes[:,1] = [i * 1.0 for i in grclayerSpikes[:,1]] 
#pclayerSpikes = pop_pclayer.getSpikes(compatible_output = True)
#pclayerSpikes[:,1] = [i * 1.0 for i in pclayerSpikes[:,1]] 
#dcnlayerSpikes = pop_dcnlayer.getSpikes(compatible_output = True)
#dcnlayerSpikes[:,1] = [i * 1.0 for i in dcnlayerSpikes[:,1]] 
#mflayerSpikes = inp_mflayer.getSpikes(compatible_output = True)
#mflayerSpikes[:,1] = [i * 1.0 for i in mflayerSpikes[:,1]] 
#iolayerSpikes = inp_iolayer.getSpikes(compatible_output = True)
#iolayerSpikes[:,1] = [i * 1.0 for i in iolayerSpikes[:,1]] 
#plot(grclayerSpikes[:,1], grclayerSpikes[:,0],".")
#plot(pclayerSpikes[:,1], pclayerSpikes[:,0],".")
#plot(dcnlayerSpikes[:,1], dcnlayerSpikes[:,0],".")
#plot(mflayerSpikes[:,1], mflayerSpikes[:,0],".")
#plot(iolayerSpikes[:,1], iolayerSpikes[:,0],".")
p.end()

