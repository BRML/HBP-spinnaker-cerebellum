#!/usr/bin/env python
import IPython
import pyNN.spiNNaker as p
from pylab import *

nn=100 # neuron count

timestep=1.0
duration=9999
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
                     

#noisepop = p.Population(nn,p.SpikeSourcePoisson,{'rate':100.,'start':5.,'duration':100.})


#prepop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(0,duration,800)],
#                                                            [i for i in arange(0,duration,80)]]*(nn/2)})
prepop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(0,duration*j/(nn+1),100)] for j in range(nn)]})
prepop.record()

#teachpop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(250,0.8*duration,100)], #]})
#                                                              [i for i in arange(250,0.8*duration,100)]]*(nn/2)})
teachpop = p.Population(nn,p.SpikeSourceArray,{'spike_times':[[i for i in arange(50,duration*j/(nn+1),100)] for j in range(nn)]})

teachpop.record()

postpop = p.Population(nn,p.IF_cond_exp,cell_params)
postpop.record()

conn0 = p.FromListConnector([(i,i,1.00,1.0) for i in range(0,nn)])

connteach = p.FromListConnector([(i,i,0.0,1.0) for i in range(nn)])
#randconn = p.FixedProbabilityConnector(0.5,weights=0.0,delays=1.0)
#noisesyn = p.Projection(noisepop,postpop,connteach,target='inhibitory')
teachsyn = p.Projection(teachpop,postpop,connteach,target='inhibitory')

# plasticity
stdp_model = p.STDPMechanism(
  timing_dependence = p.SpikePairRuleSinAdd(tau_plus = 30., tau_minus = 30.0, nearest=False, delay = 50.), #HWHM = 0.26* tau
  weight_dependence = p.AdditiveWeightDependence(w_min = 0.0, w_max = 4.0, A_plus=0.0002, A_minus = 0.000) # real As are A_*
)                                                                   #minimum: w_max=4.0, A_plus=5e-7

plasticsyn = p.Projection(prepop,postpop,conn0,
                          synapse_dynamics = p.SynapseDynamics(slow=stdp_model))
plasticsyn.projection_edge.postvertex.custom_max_atoms_per_core = 100
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

print "plastic:",plasticsyn.getWeights()
print "fixed:",teachsyn.getWeights()
show()


