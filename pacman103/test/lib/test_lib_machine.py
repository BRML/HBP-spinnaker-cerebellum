#!/usr/bin/env python
import unittest

from pacman103.lib.machine.machine import *
from pacman103.core.mapper.router import router


class MachineTests(unittest.TestCase):
    """
    Test the Machine class
    """

    def setUp(self):
        """
        Create a series of machines of various sizes in a dict
        self.test_machines {(width,height) : Machine, ...}.
        """
        self.test_machines = {}
        for x in range(1,10):
            for y in range(1,10):
                self.test_machines[(x,y)] = Machine(
                    # An arbitary hostname
                    hostname = "test_machine_%d_%d"%(x,y),
                    # The given width/height
                    x = x, y = y,
                    # The hypothetical unwrapped machine as an arbitary choice
                    type = "unwrapped",
                )


    def test_chip_creation(self):
        """
        Test that appropriate chips are created for machines of various sizes.
        """
        for (width, height), machine in self.test_machines.iteritems():
            # The number of processors created is correct for the machine size
            self.assertEqual(len(machine.get_chips()), width * height)

            # Initially none of the processors should be allocated
            self.assertEqual(len(machine.get_allocated_processors()), 0)

    def test_reordering_processor_order_when_no_chips(self):
        """
        tests if the reordering of processors so that they radiate from 00 works
        when no chips are installed
        """
        try:
            Machine(hostname = "test_machine_%d_%d"%(0,0),
                    # The given width/height
                    x = 0, y = 0,
                    # The hypothetical unwrapped machine as an arbitary choice
                    type = "unwrapped")
            raise Exception("should have raisen expcetion "
                            "due to no chip instilled at 0,0")
        except Exception as e:
            return 0




    def test_reordering_processor_order_2by2_board(self):
        machine = Machine( # An arbitary hostname
                    hostname = "test_machine_%d_%d"%(2,2),
                    # The given width/height
                    x = 2, y = 2,
                    # The hypothetical unwrapped machine as an arbitary choice
                    type = "unwrapped",)
        machine.reorder_processors_in_circle_from_00_for_palloc()
        assert(machine.free_processors[0].chip.x == 0)
        assert(machine.free_processors[0].chip.y == 0)
        assert(machine.free_processors[17].chip.x == 1)
        assert(machine.free_processors[17].chip.y == 0)
        assert(machine.free_processors[34].chip.x == 1)
        assert(machine.free_processors[34].chip.y == 1)
        assert(machine.free_processors[51].chip.x == 0)
        assert(machine.free_processors[51].chip.y == 1)

    def test_palloc(self):
        """
        Test the palloc function with constraints:
        Test 1 - allocate a vertex to (x=0,y=0,p=7)
        Test 2 - retry the same allocation - should fail
        Test 3 - allocate 15 processors (a chip's worth) to (0,0,*) & check on correct chip and not on core 7
        Test 4 - try to allocate a processor on (0,0,*) - should fail       
        Test 5 - check to ensure that 16 cores have been removed from the free pool
        Test 6 - fill the remaining cores - hooray
        Author: CP 2nd August 2013
        """

        for (width, height), machine in self.test_machines.iteritems():

            alloced_processors = set()
            num_proc_before = len(machine.get_free_processors())

            # test 1
            xtarget=0
            ytarget=0
            ptarget=7
            processorconstraint=lib_map.VertexConstraints()
            processorconstraint.x=xtarget
            processorconstraint.y=ytarget
            processorconstraint.p=ptarget
            allocproc = machine.palloc(processorconstraint)
            allocproc.placement="inuse"
            self.assertEqual(allocproc.chip.x,xtarget)
            self.assertEqual(allocproc.chip.y,ytarget)
            self.assertEqual(allocproc.idx,ptarget)
            alloced_processors.add(allocproc)

            # test 2
            with self.assertRaises(exceptions.PallocException):
                allocproc = machine.palloc(processorconstraint)
    
            #test 3
            processorconstraint.p=None
            for i in range(15):
                allocproc = machine.palloc(processorconstraint)
                allocproc.placement="inuse"
                self.assertEqual(allocproc.chip.x,xtarget)
                self.assertEqual(allocproc.chip.y,ytarget)
                self.assertNotEqual(allocproc.idx,ptarget)
                alloced_processors.add(allocproc)

            # test 4
            with self.assertRaises(exceptions.PallocException):
                allocproc = machine.palloc(processorconstraint)

            # test 5
            num_proc_avail = len(machine.get_free_processors())
            num_proc_allocated = len(machine.get_allocated_processors())
            assert num_proc_before-num_proc_avail == 16                        
            assert num_proc_allocated == 16                        

            # test 6
            for num in range(num_proc_avail):
                emptytestconstraint=lib_map.VertexConstraints()             
                p = machine.palloc(emptytestconstraint)
                p.placement="inuse"

                # Check that a processor was returned
                self.assertIsNotNone(p)

                # Check not allocated the same processor twice
                self.assertNotIn(p, alloced_processors)
                alloced_processors.add(p)

            # See that the processors requested were allocated
            num_proc_avail_after = len(machine.get_free_processors())
            num_proc_allocated_after = len(machine.get_allocated_processors())

            # No processors should be available now that they've all been
            # allocated
            self.assertEqual(num_proc_avail_after, 0)

            # The number of allocated processors should be accordingly increased
            self.assertEqual(num_proc_avail,
                             num_proc_allocated_after - num_proc_allocated)



class RouterTests(unittest.TestCase):
    """
    Test the Router class
    """

    def setUp(self):
        """
        Creates a router to perform tests on.

        This is done by creating a machine and taking the router out of an
        arbitary chip in the machine as routers require a reference to a chip
        which in turn requires a reference to a machine so this is the cleanest
        and most correct way to do this.
        """
        # Create a small machine from which we will take a processor. The type
        # chosen here is arbitary.
        self.m = Machine(hostname="m", x = 1, y = 1, type="unwrapped")

        # Take an arbitary chip from the machine.
        # XXX: This interface isn't explicitly exposed by Machine so may change
        # causing this test to fail...
        c = self.m.chips[0][0]

        # Take the router out of the chip
        # XXX: This interface isn't explicitly exposed by Chip so may change
        # causing this test to fail...
        self.router = c.router


    def test_ralloc_one_entry_per_key(self):
        """
        Test that ralloc allocates only a finite number of keys
        """
        # Mask is all-1s
        mask = -1
        m = Machine(hostname="m", x = 1, y = 1, type="unwrapped")
        # Try getting entries for as many keys as the router supports
        routing_entries = set()
        for key in range(self.router.MAX_OCCUPANCY):
            re = m.chips[0][0].router.ralloc(key, mask)
            # We got a routing entry
            self.assertIsNotNone(re)
            # It wasn't one we've seen before
            self.assertNotIn(re, routing_entries)
            routing_entries.add(re)

        # Try adding another key now that the routing table should be full, it
        # should fail
        re = m.chips[0][0].router.ralloc(-1, mask)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(m)
            raise exceptions.SystemException("didnt not cause expcetion")
        except exceptions.RouteTableDSGException as e:
            return 0


    def test_ralloc_many_entry_per_key(self):
        """
        Test that ralloc is able to have multiple entries under the same key
        """
        # Mask is all-1s
        mask = -1
        m = Machine(hostname="m", x = 1, y = 1, type="unwrapped")
        # Try getting entries for as many keys as the router supports
        routing_entries = set()
        for key in range(self.router.MAX_OCCUPANCY):
            # Add seven routing entries for each key (as there are seven routes
            # for a key in SpiNNaker)
            for entry_num in range(7):
                re = m.chips[0][0].router.ralloc(key, mask)
                # We got a routing entry
                self.assertIsNotNone(re)
                # It wasn't one we've seen before
                self.assertNotIn(re, routing_entries)
                routing_entries.add(re)

        # Try adding another key now that the routing table should be full, it
        # should fail
        re = m.chips[0][0].router.ralloc(-1, mask)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(m)
            raise exceptions.SystemException("didnt not cause expcetion")
        except exceptions.RouteTableDSGException as e:
            return 0


    def test_ralloc_with_single_mask(self):
        """
        Test that ralloc supports using a single mask for all keys
        """
        # Mask is all-1s except the bottom 2 bits
        mask = -1 << 2
        # Try getting entries for as many keys as the router supports. Note now
        # that the bottom two bits of the key are not significant and so we can
        # have four times as many keys with ascending values
        routing_entries = set()
        m = Machine(hostname="m", x = 1, y = 1, type="unwrapped")

        for key in range(m.chips[0][0].router.MAX_OCCUPANCY * 4):
            re = m.chips[0][0].router.ralloc(key, mask)
            # We got a routing entry
            self.assertIsNotNone(re)
            # It wasn't one we've seen before
            self.assertNotIn(re, routing_entries)
            routing_entries.add(re)

        # Try adding another key now that the routing table should be full, it
        # should fail
        re = m.chips[0][0].router.ralloc(-1, mask)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(m)
            raise exceptions.SystemException("didnt not cause expcetion")
        except exceptions.RouteTableDSGException as e:
            return 0





if __name__=="__main__":
    unittest.main()
