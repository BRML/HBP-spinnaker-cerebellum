# coding: utf-8
import IPython
from pylab import *
import pyNN.spiNNaker as p

rt = 10000 #runtime

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
virtual_chip_coords = {'x': 0, 'y': 12} # 12 is fine for spin5, spin3 prob. too
connected_chip_coords = {'x': 0, 'y': 0}
link=3 # 3 for spin3, 4 for spin5
tau = 100e-3

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


sample_time = 10e-3
extparams={'virtual_chip_coords':virtual_chip_coords,
                'connected_chip_coords':connected_chip_coords,
                'connected_chip_edge':link,
                'kernel_amplitude': sqrt(2e-3/sample_time),
                'output_scale' : 1.,
                'decay_factor': exp(-sample_time/tau),
                'sample_time' : sample_time * 1e3,
                'threshold' : 0,
                'motorID' : 0x110,
                'monitorID' : 0x120 }


myopop=p.Population(100,p.MyoRobotMotorControl,extparams.copy(),label='myoext')

extparams['motorID'] = 0x115
extparams['monitorID'] = 0x125

myopop2=p.Population(100,p.MyoRobotMotorControl,extparams.copy(),label='myoext')

#extpop=p.Population(1,p.ExternalSpikeSource,{'virtual_chip_coords': {'x':254,'y':255}},label='ext spikes')

# fefffe80.00000100
# set setpoint: @FEFFFE80.00000100
# set setpoint: @FEFFFE80.00000000
testpop=p.Population(200, p.IF_curr_exp, cell_params_lif, label='ifcurr')
testpop.record()

inppop=p.Population(100,p.SpikeSourcePoisson,{'rate':120,'duration':8000},label="poisson_PLOT")
inppop.stream()
inp2pop=p.Population(100,p.SpikeSourcePoisson,{'rate':50,'duration':8000})

proj=p.Projection(inppop,myopop,p.OneToOneConnector(weights=1.00,delays=1.0))
proj2=p.Projection(inp2pop,myopop2,p.OneToOneConnector(weights=1.0,delays=1.0))

#projout=p.Projection(myopop,testpop,p.OneToOneConnector(weights=0.5,delays=1.0))


#emptypop = p.Population(200, p.IF_curr_exp, cell_params_lif, label='dummy')
#dummyproj = p.Projection(emptypop, testpop, p.OneToOneConnector(weights=1.0,delays=1.0))

#inppop.record()
#myopop.record()

poispops=[]
for k,(mini,maxi) in [(0xFEFFFE21,(1220.,2880.))]: # angle measurement
#                      (0xFEFFFE03,(-20.,1000.)), # displacement
#                      (0xFEFFFE07,(-20.,1000.)), # should not go negative, but can overflow
#                      (0xFEFFFE02,(0.,1000.)), # current 
#                      (0xFEFFFE06,(0.,1000.)), # is very noisy!
#                      (0xFEFFFE00,(-800.,800.)), # omega = delta PWM, not useful!
#                      (0xFEFFFE04,(-800.,800.)), # could go much higher (~PWM=800/4000)
#                      (0xFEFFFE01,((-2<<18) + 1, (2<<18) - 1)), # spindle encoders
#                      (0xFEFFFE05,((-2<<18) + 1, (2<<18) - 1))]: # these will be auto-downscaled
    poi = p.Population(32,p.SpikeSourceRemote,{'max_rate':50,'min_rate':.1,'gauss_width':0.666,'sensormin':mini,'sensormax':maxi, 'src_type': 'rbf_det', 'listen_key': k}, label=hex(k)+"_PLOT")
    poi.record()
    poispops.append(poi)

iosource = p.Population(32,p.SpikeSourceRemote,{'max_rate':10,'min_rate':.1,'sensormin':1220,'sensormax':2880, 'src_type': 'glob_pois', 'listen_key': 0xFEFFFE30}, label=hex(k)+"_PLOT")
iosource.record()
#pois1 = p.Population(100,p.SpikeSourceRemote,{'max_rate':100,'overlap':0.2})
#pois1.record()

#errorprop=p.Projection(myopop,pois1,p.OneToOneConnector(weights=1.0,delays=1.0))

p.run(rt)
#myospikes=myopop.getSpikes()
#inpspikes=inppop.getSpikes()

#testspikes=testpop.getSpikes()
#plot(inpspikes[:,0],inpspikes[:,1],"s")
#plot(testspikes[:,0],testspikes[:,1],"s")


figure()

for i,pois1 in enumerate(poispops):
    spk=pois1.getSpikes()
#    subplot(len(poispops),1,i)
    plot(spk[:,0],spk[:,1],"s",alpha=0.4,label=pois1.vertex.label)

legend()

figure()
spk=iosource.getSpikes()
plot(spk[:,0],spk[:,1],"s",alpha=0.4,label=pois1.vertex.label)
#figure()

#spk=inppop.getSpikes()
#plot(spk[:,0],spk[:,1],"s",alpha=0.4,label=pois1.vertex.label)


IPython.embed()
#show()
