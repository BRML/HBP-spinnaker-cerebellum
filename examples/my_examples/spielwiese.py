#!/usr/bin/env python
import IPython
import pyNN.spiNNaker as p
#import pyNN.neuron as p
from pylab import *
from pyNN.utility import init_logging
from pyNN.utility import get_script_args
from pyNN.errors import RecordingError

spin_control = p.setup(timestep=0.1, min_delay=0.1, max_delay=4.0)
#init_logging("logfile", debug=True)

ifcell = p.Population(10, p.IF_cond_exp, {  'i_offset' : 0.1,    'tau_refrac' : 3.0,
                                'v_thresh' : -51.0,  'tau_syn_E'  : 2.0,
                                'tau_syn_I': 5.0,    'v_reset'    : -70.0,
                                'e_rev_E'  : 0.,     'e_rev_I'    : -80.}, label = "myFinalCell_PLOT")

spike_sourceE = p.Population(10, p.SpikeSourceArray, {'spike_times': [float(i) for i in range(0,9000,100)]}, label = "mySourceE_PLOT")
spike_sourceI = p.Population(10, p.SpikeSourceArray, {'spike_times': [float(i) for i in range(1000,5000,50)]}, label = "mySourceI_PLOT")

connE = p.Projection(spike_sourceE, ifcell, p.AllToAllConnector(weights=1.0, delays=0.2), target='excitatory')
connI = p.Projection(spike_sourceI, ifcell, p.AllToAllConnector(weights=3.0, delays=0.2), target='inhibitory')

#p1 = Population(100, IF_curr_alpha, structure=space.Grid2D())

#prepop = p.Population(100 ,p.SpikeSourceArray,{'spike_times':[[i for i in arange(10,duration,100)], [i for i in arange(50,duration,100)]]*(nn/2)})


#prj2_1 = Projection(p2, p1, method=AllToAllConnector(), target='excitatory')


#p1.record()	# record spike times

spike_sourceE.record()
spike_sourceI.record()
ifcell.record()
ifcell.record_v()

try:
	ifcell.record_gsyn("Results/IF_cond_exp_spinnaker.gsyn")
except (NotImplementedError, RecordingError):
	pass

#p.run(10000.0)
p.run(10000.0, do_load = True, do_run = False)
# here you could do something in between; note that this split will only work with this spinnaker_package!
#IPython.embed()
spin_control.run(spin_control.dao.app_id)

w_f = open('Results/einfache-spielwieseE.weights', 'w')
w_connE = connE.getWeights(format='list')
#w_f.write("%i\n" % len(w_connE))
for item in w_connE:
	w_f.write("%s\n" % item)
w_f.close()

w_f = open('Results/einfache-spielwieseI.weights', 'w')
w_connI = connI.getWeights(format='list')
#w_f.write("%i\n" % len(w_connI))
for item in w_connI:
	w_f.write("%s\n" % item)
w_f.close()

spikes1 = spike_sourceE.getSpikes()
spikes2 = spike_sourceI.getSpikes()
spikes3 = ifcell.getSpikes()
ifcellV = ifcell.get_v()

if p.__name__ == 'pyNN.spiNNaker':
	for item in spikes1: item[0], item[1] = item[1], item[0]
	for item in spikes2: item[0], item[1] = item[1], item[0]
	for item in spikes3: item[0], item[1] = item[1], item[0]
	for item in ifcellV: item[0], item[1] = item[1], item[0]

sp1_f = open('Results/simpleNetwork_spike_sourceE.dat', 'w')
for item in spikes1: sp1_f.write("%s\t%s\n" % (item[0], item[1]))
sp1_f.close()

sp2_f = open('Results/simpleNetwork_spike_sourceI.dat', 'w')
for item in spikes2: sp2_f.write("%s\t%s\n" % (item[0], item[1]))
sp2_f.close()

sp3_f = open('Results/simpleNetwork_spike_ifcell', 'w')
for item in spikes3: sp3_f.write("%s\t%s\n" % (item[0], item[1]))
sp3_f.close()

v1_f = open('Results/simpleNetwork_v_ifcell.dat', 'w')
for item in ifcellV: v1_f.write("%s\t%s\n" % (item[0], item[1]))
v1_f.close()

#plot(spikes1[:,1],spikes1[:,0],"gd",markersize=10,alpha=0.6)
#plot(spikes2[:,1],spikes2[:,0]+1,"ro",markersize=10,alpha=0.6)
#plot(spikes3[:,1],spikes3[:,0]+2,"bs",markersize=10,alpha=0.6)
#show()

#plot(ifcellV[:,1],ifcellV[:,2])
#show()

p.end()
