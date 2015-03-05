#!/usr/bin/python
"""
"""
import numpy
import sys
import pacman103.front.pynn as p
import visualiser.visualiser_modes as vm


import retina_lib
#import gaborcreatejose as retina_lib
#import gaussiancreatejose as retina_lib

FWD = 0
BWD = 1

input_size = 128             # Size of each population
subsample_size = 32
runtime = 60000*2
#runtime = 60
n_orientations = 4

size_gabor = 7

# Simulation Setup
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 11.0)            # Will add some extra parameters for the spinnPredef.ini in here

p.set_number_of_neurons_per_core('IF_curr_exp', 128)      # this will set one population per core

cell_params = { 'tau_m' : 64, 'i_offset'  : 0,
    'v_rest'    : -75,  'v_reset'    : -95, 'v_thresh'   : -40,
    'tau_syn_E' : 15,   'tau_syn_I'  : 15,  'tau_refrac' : 2}


cell_params_subsample = { 'tau_m' : 32, 'i_offset'  : 0,
    'v_rest'    : -75,  'v_reset'    : -95, 'v_thresh'   : -40,
    'tau_syn_E' : 15,   'tau_syn_I'  : 15,  'tau_refrac' : 2}


cell_params_or = { 'tau_m' : 24, 'i_offset'  : 0,
    'v_rest'    : -75,  'v_reset'    : -95, 'v_thresh'   : -40,
    'tau_syn_E' : 20,   'tau_syn_I'  : 15,  'tau_refrac' : 2}


cell_params_detector = { 'tau_m' : 24, 'i_offset'  : 0,
    'v_rest'    : -75,  'v_reset'    : -75, 'v_thresh'   : -65,
    'tau_syn_E' : 20,   'tau_syn_I'  : 15,  'tau_refrac' : 2}

v_init = -75

#external stuff population requiremenets
connected_chip_coords = {'x': 0, 'y': 0}
virtual_chip_coords = {'x': 0, 'y': 5}
link = 4


print "Creating input population: {} x {}".format(input_size, input_size)

input_pol_1_up = p.Population(128*128,
                           p.ExternalRetinaDevice,
                           {'virtual_chip_coords': virtual_chip_coords,
                            'connected_chip_coords':connected_chip_coords,
                            'connected_chip_edge':link,
                            'position': p.ExternalRetinaDevice.RIGHT_RETINA,
                            'polarity': p.ExternalRetinaDevice.UP_POLARITY},
                           label='input_pol1')

input_pol_1_down = p.Population(128*128,
                           p.ExternalRetinaDevice,
                           {'virtual_chip_coords': virtual_chip_coords,
                            'connected_chip_coords':connected_chip_coords,
                            'connected_chip_edge':link,
                            'position': p.ExternalRetinaDevice.RIGHT_RETINA,
                            'polarity': p.ExternalRetinaDevice.DOWN_POLARITY},
                           label='input_pol1')

#virtual_chip_coords = {'x': 254, 'y': 250}
input_pol_2_up = p.Population(128*128,
                           p.ExternalRetinaDevice,
                           {'virtual_chip_coords': virtual_chip_coords,
                            'connected_chip_coords':connected_chip_coords,
                            'connected_chip_edge':link,
                            'position': p.ExternalRetinaDevice.LEFT_RETINA,
                            'polarity': p.ExternalRetinaDevice.UP_POLARITY},
                           label='input_pol2')

input_pol_2_down = p.Population(128*128,
                           p.ExternalRetinaDevice,
                           {'virtual_chip_coords': virtual_chip_coords,
                            'connected_chip_coords':connected_chip_coords,
                            'connected_chip_edge':link,
                            'position':p.ExternalRetinaDevice.LEFT_RETINA,
                            'polarity': p.ExternalRetinaDevice.DOWN_POLARITY},
                           label='input_pol2')


#input_pol_1_up.record(visualiser_mode=vm.TOPOLOGICAL, visualiser_2d_dimension={'x':128, 'y':128})
#input_pol_1_down.record(visualiser_mode=vm.TOPOLOGICAL, visualiser_2d_dimension={'x':128, 'y':128})

#input_pol_1 = p.Population(128*128, p.ProxyNeuron, {'x_source':254, 'y_source':254}, label='input_pol1')
#input_pol_1.set_mapping_constraint({'x':1,'y':0})                   # this is where the sensor is going to be actually mapped in the NN

#input_pol_2 = p.Population(128*128, p.ProxyNeuron, {'x_source':254, 'y_source':250}, label='input_pol2')
#input_pol_2.set_mapping_constraint({'x':1,'y':0})                   # this is where the sensor is going to be actually mapped in the NN




subsampled = p.Population(subsample_size*subsample_size,         # size
                          p.IF_curr_exp,   # Neuron Type
                          cell_params_subsample,   # Neuron Parameters
                          label="Input") # Label
subsampled.initialize('v', -75)

subsampled.set_mapping_constraint({'x':0,'y':1})
#subsampled.record()     # sends spikes to the visualiser (use parameters = 32)


p1_up = p.Projection(input_pol_1_up, subsampled, p.FromListConnector(retina_lib.subSamplerConnector2D(128,subsample_size,.2,1)), label='subsampling projection')
p1_down = p.Projection(input_pol_1_down, subsampled, p.FromListConnector(retina_lib.subSamplerConnector2D(128,subsample_size,.2,1)), label='subsampling projection')
p2_up = p.Projection(input_pol_2_up, subsampled, p.FromListConnector(retina_lib.subSamplerConnector2D(128,subsample_size,.2,1)), label='subsampling projection')
p2_down = p.Projection(input_pol_2_down, subsampled, p.FromListConnector(retina_lib.subSamplerConnector2D(128,subsample_size,.2,1)), label='subsampling projection')

orientations = list()
#gabor = retina_lib.GaborConnectorList(2, n_orientations, size_gabor)
gaussians = retina_lib.gaussians(orientations=n_orientations,size=size_gabor, sigma=.75)

#for g in gaussians:
#    print g
#    retina_lib.show_kernel(g)


projections_orientations = list()


# subsampled to orientation
for i in range(n_orientations):
    orientations.append(p.Population(subsample_size*subsample_size,         # size
                           p.IF_curr_exp,   # Neuron Type
                           cell_params_or,   # Neuron Parameters
                           label="orientation_%d" % i )) # Label

    conn_list = retina_lib.Filter2DConnector(   subsample_size,
                                    subsample_size,
                                    size_gabor,
                                    1,
                                    gaussians[i],
                                    delays=1, gain=.5, precision=8)


    projections_orientations.append(p.Projection(subsampled, orientations[i],
                                        p.FromListConnector(conn_list), label='orientation_%d' % i))


projections_wta = []
for i in range(n_orientations):
    for j in range(n_orientations):
        if i != j:
            print "Inhibiting orientation", j, "from orientation",i
            #projections_wta.append(p.Projection(orientations[i], orientations[j], p.OneToOneConnector(weights= -1, delays=1), target='inhibitory'))
            pass

#orientations[0].set_mapping_constraint({'x':0,'y':1})
#orientations[0].record()

#orientations[0].record_v()


# plus and cross detectors
plus_detector = p.Population(subsample_size*subsample_size,         # size
                           p.IF_curr_exp,   # Neuron Type
                           cell_params_detector,   # Neuron Parameters
                           label="plus_detector") # Label
plus_detector.initialize('v', -75)

cross_detector = p.Population(subsample_size*subsample_size,         # size
                           p.IF_curr_exp,   # Neuron Type
                           cell_params_detector,   # Neuron Parameters
                           label="cross_detector") # Label
cross_detector.initialize('v', -75)


pooling_size = 5
#prox_list =  retina_lib.ProximityConnector(subsample_size, subsample_size, pooling_size,
#                                        3, 1, allow_self_connections=True)

prox_list = retina_lib.Filter2DConnector(subsample_size,
                                    subsample_size,
                                    pooling_size,
                                    jump=1,
                                    weights=numpy.ones(pooling_size*pooling_size),
                                    delays=1, gain=.25, precision=8)

#print prox_list

#plus_proj1 = p.Projection(orientations[retina_lib.H], plus_detector, p.OneToOneConnector(weights = 5, delays =1), target='excitatory')
#plus_proj2 = p.Projection(orientations[retina_lib.V], plus_detector, p.OneToOneConnector(weights = 5, delays =1), target='excitatory')

plus_proj1 = p.Projection(orientations[retina_lib.H], plus_detector, p.FromListConnector(prox_list))
plus_proj2 = p.Projection(orientations[retina_lib.V], plus_detector, p.FromListConnector(prox_list))

cross_proj1 = p.Projection(orientations[retina_lib.DEG45], cross_detector, p.FromListConnector(prox_list))
cross_proj2 = p.Projection(orientations[retina_lib.DEG135], cross_detector, p.FromListConnector(prox_list))


wta_prox_list = retina_lib.Filter2DConnector(subsample_size,
                                    subsample_size,
                                    pooling_size,
                                    jump=1,
                                    weights=numpy.ones(pooling_size*pooling_size),
                                    delays=1, gain=-.25, precision=8)

#print wta_prox_list

inh1 = p.Projection(cross_detector, plus_detector, p.FromListConnector(wta_prox_list), target='inhibitory')
inh2 = p.Projection(plus_detector, cross_detector, p.FromListConnector(wta_prox_list), target='inhibitory')

#cross_detector.record()
#cross_detector.set_mapping_constraint({'x':1,'y':0})

#orientations[2].set_mapping_constraint({'x':1,'y':0})
#orientations[2].record()

#motor
output = p.Population(      n_orientations,         # size
                            p.IF_curr_exp,   # Neuron Type
                            cell_params_detector,   # Neuron Parameters
                            label="output") # Label

robot_motor_control = p.Population(n_orientations,         # size
                            p.RobotMotorControl,   # Neuron Type
                            {'virtual_chip_coords': virtual_chip_coords,
                            'connected_chip_coords':connected_chip_coords,
                            'connected_chip_edge':link},   # Neuron Parameters
                            label="robot pop") # Label

output.record(visualiser_mode=vm.RASTER)
#robot_motor_control.record(visualiser_mode=vm.RASTER)
#robot_motor_control.record(visualiser_mode=vm.RASTER)

#for i in range(n_orientations):
#    p.Projection(orientations[i], output, p.FromListConnector(
#        retina_lib.AllToOne(subsample_size*subsample_size, i, 1, 1)), target='excitatory')

out1 = p.Projection(plus_detector, output, p.FromListConnector(
        retina_lib.AllToOne(subsample_size*subsample_size, BWD, .25, 1)), target='excitatory')
#check between forward and backwards and what will happen if left and right directions are given
out2 = p.Projection(cross_detector, output, p.FromListConnector(
        retina_lib.AllToOne(subsample_size*subsample_size, FWD, .25, 1)), target='excitatory')


inh_out_1 = p.Projection(output, output, p.AllToAllConnector(weights=-5, delays=1, allow_self_connections=False), target='inhibitory')
robot_projections = p.Projection(output, robot_motor_control, p.OneToOneConnector(weights=-5, delays=1), target='excitatory')

#output.set_robotic_output()
#output1.set_mapping_constraint({'x':0,'y':0})

p.run(runtime)              # Simulation time
p.end()