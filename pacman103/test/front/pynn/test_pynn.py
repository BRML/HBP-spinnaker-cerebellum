#!/usr/bin/env python
import pickle
import pylab
import unittest

import pacman103.front.pynn as pynn



class NeuronTestCase(unittest.TestCase):
    """
    COMMENT ME
    This test has 'amu15' hard coded on it, and must be up to work correctly
    """

    def test_lif_current(self):
        """
        Simulates one LIF neuron and checks the membrane-potential trace matches
        reference data.

        TODO add assertion on comparison, rather than just graphing the result.
        TODO take parameter for machine hostname.
        """
        print "test_lif_current..."
        pynn.setup(**{'machine':'bluu', 'debug':False}) #TODO take machine parameter
        lif = {"v_rest":-70.0, "v_reset":-70.0, "v_thresh":-50.0,  # mV
               "tau_m":40.0, "tau_syn_E":20.0, "tau_syn_I":5.0,    # mS
               "tau_refrac":1.0, "cm":40.0/50.0, "i_offset":0.0}   # ms, nF, nA
        pop = pynn.Population(1, pynn.IF_curr_exp, lif)
        pop.set("i_offset", 0.5)
        pop.record_v()
        pynn.run(1000)

        with open('data/test_lif_current.pickle', 'r') as f:
            data = f.read()
            trace = pickle.loads(data)

        fig = pylab.figure(figsize=(8.0, 5.7))
        ax = fig.add_subplot(1,1,1)
        ax.plot(pop.get_v()[:,2])
        ax.plot(trace)

        pylab.show()
        pynn.end()


if __name__=="__main__":
    unittest.main()
