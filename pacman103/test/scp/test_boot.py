'''
Created on 31 Jan 2014

@author: zzalsar4
'''
from pacman103.scp.boot import boot, _readstruct, _readconf
import unittest

class BootTests(unittest.TestCase):

    def test__readstruct(self):
        sv = _readstruct("sv_t", "spinnaker_tools/boot/sark.struct")
        print sv
        
    def test__readconf(self):
        sv = dict()
        sv["p2p_dims"] = [0, 0, 0, 0, 0]
        sv["hw_ver"] = [0, 0, 0, 0, 0]
        sv["cpu_clk"] = [0, 0, 0, 0, 0]
        sv["led0"] = [0, 0, 0, 0, 0]
        _readconf(sv, "spinnaker_tools/boot/spin2.conf")
        print sv
        
    def test_bootboard(self):
        boot("spinn-10.cs.man.ac.uk", "spinnaker_tools/boot/scamp-120.boot", "spinnaker_tools/boot/spin2.conf", "spinnaker_tools/boot/sark.struct")

if __name__ == "__main__":
    unittest.main()
