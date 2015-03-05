"""
Test example, for getting PACMAN103 up and running
"""
#!/usr/bin/python
import pacman103.front.pynn as p
import numpy, pylab
import os

#p.setup(timestep=1.0, min_delay = 1.0, max_delay = 8.0, machine="amu12", output=os.getcwd(), db_name='simple_test.sqlite')
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 8.0, machine="spinn-7", output=os.getcwd(), db_name='simple_test.sqlite')

n_pop = 16    # number of populations
nNeurons = 200  # number of neurons in each population


cell_params_lif_in = { 'tau_m'      : 32,
                'cm'        : 0.35,     # added to make PACMAN103 work
                'v_init'    : -80,
                'v_rest'     : -75,   
                'v_reset'    : -95,  
                'v_thresh'   : -55,
                'tau_syn_E'   : 5,
                'tau_syn_I'   : 10,
                'tau_refrac'   : 100, 
                'i_offset'   : 1
                }

cell_params_lif = { 'tau_m'      : 32,
                'cm'        : 0.35,     # added to make PACMAN103 work
                'v_init'    : -80,
                'v_rest'     : -70,   
                'v_reset'    : -95,  
                'v_thresh'   : -55,
                'tau_syn_E'   : 5,
                'tau_syn_I'   : 10,
                'tau_refrac'   : 5,                 
                'i_offset'   : 0
                }

populations = list()
projections = list()

populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif_in, label='pop_0'))

populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))  

projections.append(p.Projection(populations[0], populations[1], p.OneToOneConnector(weights=8, delays=16)))

populations[0].set_mapping_constraint({'x':7, 'y':7})
populations[1].set_mapping_constraint({'x':3, 'y':4})

p.run(3000)

