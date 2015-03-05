"""
Synfirechain-like example
"""
#!/usr/bin/python
import pacman103.front.pynn as p
import numpy, pylab

#p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.set_number_of_neurons_per_core("IF_curr_exp", 100)

nNeurons = 200 # number of neurons in each population

cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -65.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -64.4
                     }

populations = list()
projections = list()

weight_to_spike = 2
delay = 3.2

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, delay)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_1'))
populations[0].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_2'))
populations[1].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_3'))
populations[2].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_4'))
populations[3].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_5'))
populations[4].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_6'))
populations[5].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_7'))
populations[6].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_8'))
populations[7].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_9'))
populations[8].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_10'))
populations[9].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_11'))
populations[10].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_12'))
populations[11].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_13'))
populations[12].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_14'))
populations[13].set_mapping_constraint({'x':0,'y':0})
populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_15'))
populations[14].set_mapping_constraint({'x':0,'y':0})

populations.append(p.Population(100, p.IF_curr_exp, cell_params_lif, label='pop_16'))
populations[15].set_mapping_constraint({'x':4,'y':3})



projections.append(p.Projection(populations[0], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[1], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[2], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[3], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[4], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[5], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[6], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[7], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[8], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[9], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[10], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[11], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[12], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[13], populations[15], p.FromListConnector(injectionConnection)))
projections.append(p.Projection(populations[14], populations[15], p.FromListConnector(injectionConnection)))


#populations[0].record_v()
#populations[0].record_gsyn()
#populations[0].record()

p.run(1000)

v = None
gsyn = None
spikes = None

v = populations[0].get_v()
#gsyn = populations[0].get_gsyn()
spikes = populations[0].getSpikes()

if spikes != None:
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".") 
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

# Make some graphs
ticks = len(v) / nNeurons

if v != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for pos in range(0, nNeurons, 20):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in v_for_neuron], 
                [i[2] for i in v_for_neuron])
    pylab.show()

if gsyn != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn')
    pylab.title('gsyn')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in gsyn_for_neuron], 
                [i[2] for i in gsyn_for_neuron])
    pylab.show()

p.end()