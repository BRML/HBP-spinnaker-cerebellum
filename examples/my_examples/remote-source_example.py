# coding: utf-8
import IPython
from pylab import *
import pyNN.spiNNaker as p
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)

cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 20.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 5.0,
                     'tau_syn_I' : 5.0,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -60.0
                     }


#extpop=p.Population(1,p.ExternalSpikeSource,{'virtual_chip_coords': {'x':254,'y':255}},label='ext spikes')

# fefffe80.00000100
# set setpoint: @FEFFFE80.00000100
# set setpoint: @FEFFFE80.00000000
testpop=p.Population(200, p.IF_curr_exp, cell_params_lif, label='ifcurr')
testpop.record()

pois1 = p.Population(32,p.SpikeSourceRemote,{'max_rate':100,'min_rate':0.1,'overlap':2e-8,'sensormin':0,'sensormax':8191, 'src_type': 'rbf_pois'})

pois1.record()

#errorprop=p.Projection(myopop,pois1,p.OneToOneConnector(weights=1.0,delays=1.0))

p.run(20000)
spk=pois1.getSpikes()

figure()
plot(spk[:,0],spk[:,1],"s")

figure()
hist(spk[:,1],bins=32)

IPython.embed()
p.end()

