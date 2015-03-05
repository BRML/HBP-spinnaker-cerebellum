# coding: utf-8
import IPython
import time
from pylab import *
import pyNN.spiNNaker as p

import serial
sio = serial.Serial('/dev/ttyUSB0', 4000000, rtscts=True, dsrdtr=True, timeout=1)
sio.write("#000007F1.00000004\n")
time.sleep(0.1)
sio.write("#00000380.01200110\n")
time.sleep(0.1)
sio.write("#00000381.01250115\n")
time.sleep(0.1)
sio.write("#000003B0.0000000d\n")
time.sleep(0.1)
sio.write("#000003B1.0000000d\n")
time.sleep(0.1)
sio.write("#000003C0.00000050\n")

sio.close()

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

poispops=[]
for k,(mini,maxi) in [(0xFEFFFE20,(1220.,2880.)),
                      (0xFEFFFE03,(-20.,500.)),
                      (0xFEFFFE07,(-20.,500.)),
                      (0xFEFFFE02,(0.,1000.)),
                      (0xFEFFFE06,(0.,1000.)),
                      (0xFEFFFE00,(-50.,50.)),
                      (0xFEFFFE04,(-50.,50.))]:
    poi = p.Population(32,p.SpikeSourceRemote,{'max_rate':100,'min_rate':.1,'overlap':10./(maxi-mini),'sensormin':mini,'sensormax':maxi, 'src_type': 'rbf_pois', 'listen_key': k})
    poi.record()
    poispops.append(poi)
    

#errorprop=p.Projection(myopop,pois1,p.OneToOneConnector(weights=1.0,delays=1.0))

p.run(15000)

figure()

for i,pois1 in enumerate(poispops):
    spk=pois1.getSpikes()
#    subplot(len(poispops),1,i)
    plot(spk[:,0],spk[:,1],"s",alpha=0.4)

#figure()
#hist(spk[:,1],bins=32)

IPython.embed()
p.end()

