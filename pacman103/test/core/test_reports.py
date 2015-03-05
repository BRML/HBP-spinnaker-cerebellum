#!/usr/bin/env python

import unittest
import tempfile
from array import array
from random import randint
from pacman103.core import reports
from pacman103.lib.machine.chip import Chip
from pacman103.lib.machine.machine import Machine
from pacman103.core.dao import DAO
import os

class ReportTestCase(unittest.TestCase):
   
    def test_generate_router_report(self):
       
        # Write a temporary router dat file 
        # (assumption is that the filename ends with .dat)
        (routeFile, routeFileName) = tempfile.mkstemp(".dat")
        routeFile = os.fdopen(routeFile, "wb")
        print "Test writing route file to %s" % (routeFileName)
       
        # Write some random routes
        route_id = 0
        no_routes = 35
        for i in range(0, no_routes):
            compiled = route_id | (no_routes << 16)
            routeValue = randint(0, 0x3F) | (randint(1, 16) << 6)
            maskedkey = (randint(0, 7) << 24 | randint(0, 7) << 16 
                | randint(0, 16) << 11)
            mask = 0xFFFFFC00
            output_me = array('I', [compiled, routeValue, maskedkey, mask])
            output_me.tofile(routeFile)
            route_id += 1
        
        compiled=mykey=mymask=myroute=0xFFFFFFFF
        output_me = array('I', [compiled, mykey, mymask, myroute])
        output_me.tofile(routeFile)
        routeFile.close()
        
        dao = DAO(None, hostname="amu12")
        chip = Chip(dao.machine, 0, 0, None, 16)
        
        print "Running read of generated route"
        reports.generate_router_report(routeFileName, chip, dao)
        
        os.remove(routeFileName)
if __name__=="__main__":
    unittest.main()
