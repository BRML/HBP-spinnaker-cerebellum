#!/usr/bin/env python
import IPython
import pyNN.spiNNaker as p
from pylab import *

p.setup(timestep=1.0,min_delay=1.0,max_delay=10.0)

pois1 = p.Population(100,p.SpikeSourceRemote,{'max_rate':50,'overlap':0.2})

pois1.record()

p.run(1000.)

spk=pois1.getSpikes()

figure()
plot(spk[:,0],spk[:,1],"s")

figure()
hist(spk[:,1])
#IPython.embed()
show()
