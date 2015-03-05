# Import pacman
from pacman103.front import pynengo as spinnaker

# Import nengo
import nengo

# Import unittest and the like
import unittest, logging
logging.basicConfig(level=logging.INFO)

class BuilderTest( unittest.TestCase ):
    def testEnsemble( self ):
        # Create a simple model containing a single projection
        model = nengo.Model( "Test Model" )

        # Add an ensemble to the model
        a = model.make_ensemble( "A", nengo.LIF(100), 1 )
        b = model.make_ensemble( "B", nengo.LIF(200), 1 )

        # Add some connections
        model.connect( 'A', 'B' )

        # Now try to build the model
        sim = model.simulator( sim_class=spinnaker.Simulator,
                               hostname = "spinn-7" )

        # Now verify various aspects of the build

if __name__ == "__main__":
    unittest.main()
