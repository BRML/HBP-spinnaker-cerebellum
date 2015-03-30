#!/usr/bin/env python
import IPython
import pyNN.spiNNaker as p
from pylab import *

nn_pre=1000
nn_post=16
nn_teach=16 # neuron count

timestep=0.6
duration=100*1000
p.setup(timestep=timestep,min_delay=timestep,max_delay=10.0)
#p.set_number_of_neurons_per_core("IF_cond_exp", 12)
cell_params = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 2.5,
                     'tau_syn_I' : 2.5,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -54.4
                     }
                     
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

cell_params=cellparams_pclayer
#noisepop = p.Population(nn,p.SpikeSourcePoisson,{'rate':100.,'start':5.,'duration':100.})


#prepop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(0,duration,800)],
#                                                            [i for i in arange(0,duration,80)]]*(nn/2)})
#prepop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(0,duration*j/(nn+1),100)] for j in range(nn)]})
prepop = p.Population(nn_pre,p.SpikeSourcePoisson,{'rate':40,'duration':duration})
#prepop.record()

#teachpop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(250,0.8*duration,100)], #]})
#                                                              [i for i in arange(250,0.8*duration,100)]]*(nn/2)})
#teachpop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i f)
teachpop = p.Population(nn_teach,p.SpikeSourcePoisson,{'rate':50,'duration':duration})


#teachpop.record()

postpop = p.Population(nn_post,p.IF_cond_exp,cell_params)
#postpop.record()


connteach = p.OneToOneConnector(weights=0.0,delays=1.0) #FromListConnector([(i,i,0.0,1.0) for i in range(nn)])
#randconn = p.FixedProbabilityConnector(0.5,weights=0.0,delays=1.0)
#noisesyn = p.Projection(noisepop,postpop,connteach,target='inhibitory')
teachsyn = p.Projection(teachpop,postpop,connteach,target='inhibitory')

# plasticity

wdep_grcpcsynapsis = p.AdditiveWeightDependence(w_min = 0.0, w_max = 0.5, A_plus = 0.0015, A_minus = 0.0018)
tdep_grcpcsynapsis = p.SpikePairRuleSinAdd(tau_minus = 50., tau_plus = 50., delay = 100.0, nearest = False ) # delay 70-100
stdp_grcpcsynapsis = p.STDPMechanism(timing_dependence = tdep_grcpcsynapsis, weight_dependence = wdep_grcpcsynapsis, voltage_dependence = None )
syndyn_grcpcsynapsis = p.SynapseDynamics( slow = stdp_grcpcsynapsis)

rng = p.NumpyRNG()
grcpc_weights_distribution = p.RandomDistribution('uniform',[0.05,0.5],rng)
pro_grcpcsynapsis_connector = p.FixedProbabilityConnector(0.8,weights=grcpc_weights_distribution)
pro_grcpcsynapsis_left = p.Projection(prepop, postpop, pro_grcpcsynapsis_connector, target = "excitatory" , synapse_dynamics = syndyn_grcpcsynapsis, label = "grcpcsynapsis")

proj = pro_grcpcsynapsis_left
proj.projection_edge.postvertex.custom_max_atoms_per_core = max(1,4000 / proj.projection_edge.prevertex.atoms)

#plasticsyn.projection_edge.postvertex.custom_max_atoms_per_core = 100
p.run(duration)
#IPython.embed()

prespikes = prepop.getSpikes()

if prespikes != None:
    plot(prespikes[:,0],prespikes[:,1],"gd",markersize=10,alpha=0.6)

teachspikes = teachpop.getSpikes()
if teachspikes != None:
    plot(teachspikes[:,0],teachspikes[:,1],"ro",markersize=10,alpha=0.6)

postspikes = postpop.getSpikes()
if postspikes != None:
    plot(postspikes[:,0],postspikes[:,1],"bs",markersize=10,alpha=0.6)

#print "plastic:",plasticsyn.getWeights()
#print "fixed:",teachsyn.getWeights()
show()


