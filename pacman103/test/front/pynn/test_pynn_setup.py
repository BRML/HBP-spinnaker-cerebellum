#!/usr/bin/env python
import unittest
import pacman103

import pacman103.front.pynn as pynn

class PyNNTests(unittest.TestCase):
    """
    Test the Machine class
    """

    def test_pynn_basic(self):
        pass
        """
        TODO figure out how to take machine name as a parameter
        """
        print "test_pynn_basic setup....."
        pynn.setup(**{'machine':'spinn-7'})

        n_atoms = 10

        proj1_params = {'source': None, 'delays': 1, 'weights': 1, 'target': 'excitatory'}
        proj2_params = {'allow_self_connections': True, 'delays': 2,
            'p_connect': 0.1, 'weights': 2, 'source': None, 'target': None}


        cell_params = { 'tau_m' : 64, 'v_init'  : -75, 'i_offset'  : 0,
                'v_rest'    : -75,  'v_reset'    : -95, 'v_thresh'   : -40,
                'tau_syn_E' : 15,   'tau_syn_I'  : 15,  'tau_refrac' : 10}


        pop1 = pynn.Population(n_atoms, pynn.IF_curr_exp, cell_params, label='pop1')
        pop2 = pynn.Population(n_atoms*2, pynn.IF_curr_exp, cell_params, label='pop2')

        proj1 = pynn.Projection(pop1, pop2, pynn.OneToOneConnector(weights=1, delays=1), target='excitatory')
        proj2 = pynn.Projection(pop1, pop2, pynn.FixedProbabilityConnector(weights=2, delays=2, p_connect=.1))

        pynn.controller.map_model()         # at this stage the model is mapped
        print "checking vertices..."
        self.assertEqual(pop1.vertex.parameters, cell_params)
        self.assertEqual(pynn.controller.dao.vertices[1].parameters, cell_params)

        self.assertEqual(pop1.vertex.model, pacman103.front.pynn.models.IF_curr_exp)
        self.assertEqual(pynn.controller.dao.vertices[0].label, "pop1")
        self.assertEqual(pynn.controller.dao.vertices[1].label, "pop2")

        self.assertEqual(pop1.vertex.atoms, n_atoms)
        self.assertEqual(pynn.controller.dao.vertices[1].atoms, n_atoms*2)

        print "checking edges..."
        self.assertEqual(pynn.controller.dao.edges[0].model, pacman103.front.pynn.connectors.OneToOneConnector)
        self.assertEqual(proj2.edge.model, pacman103.front.pynn.connectors.FixedProbabilityConnector)


        self.assertEqual(proj1.edge.parameters, proj1_params)
        self.assertEqual(pynn.controller.dao.edges[1].parameters, proj2_params)

        # testing the mapping phase
        self.assertEqual(len(pynn.controller.dao.subedges), 2)
        self.assertEqual(len(pynn.controller.dao.subvertices), 2)

        self.assertEqual(len(pynn.controller.dao.routings), 2)

#        pynn.run(100)
        pynn.end()



if __name__=="__main__":
    unittest.main()
