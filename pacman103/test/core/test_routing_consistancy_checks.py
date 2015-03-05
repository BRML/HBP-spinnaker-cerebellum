__author__ = 'stokesa6'


import unittest

from pacman103.core.mapper.router import router
from pacman103.lib.machine import machine as lib_machine
from pacman103.core.dao import DAO
from pacman103.core import exceptions
import random

class TestRoutingConsistancyChecks(unittest.TestCase):

    @staticmethod
    def test_maxiumum_test_case_fail_edge_case_spinn7():
        machine = lib_machine.Machine('spinn-7', type="spinn4")
        chip_router = machine.get_chip(0, 0).router
        for index in range(1000):
            chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over "
                                             "the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0

    @staticmethod
    def test_maxiumum_test_case_success_edge_case_spinn7():
        machine = lib_machine.Machine('spinn-7', type="spinn4")
        chip_router = machine.get_chip(0, 0).router
        for index in range(999):
            chip_router.ralloc(index, 0xffffffff)
        router.Router.check_for_table_supassing_maxiumum_level(machine)
        return 0

    @staticmethod
    def  test_maxiumum_test_case_fail_spinn7():
        machine = lib_machine.Machine('spinn-7', type="spinn4")
        chip_router = machine.get_chip(0, 0).router
        for index in range(1010):
            chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over"
                                             " the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0


    @staticmethod
    def test_maxiumum_test_case_success_spinn7():
        machine = lib_machine.Machine('spinn-7', type="spinn4")
        chip_router = machine.get_chip(0, 0).router
        for index in range(10):
            chip_router.ralloc(index, 0xffffffff)
        router.Router.check_for_table_supassing_maxiumum_level(machine)
        return 0

    @staticmethod
    def  test_maxiumum_test_case_multiple_fail_spinn7():
        machine = lib_machine.Machine('spinn-7', type="spinn4")
        first_chip_router = machine.get_chip(0, 0).router
        second_chip_router = machine.get_chip(0, 0).router
        for index in range(1010):
            first_chip_router.ralloc(index, 0xffffffff)
            second_chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over"
                                             " the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0




    @staticmethod
    def test_maxiumum_test_case_fail_edge_case_spinn2():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        chip_router = machine.get_chip(0, 0).router
        for index in range(1000):
            chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over "
                                             "the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0

    @staticmethod
    def test_maxiumum_test_case_success_edge_case_spinn2():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        chip_router = machine.get_chip(0, 0).router
        for index in range(999):
            chip_router.ralloc(index, 0xffffffff)
        router.Router.check_for_table_supassing_maxiumum_level(machine)
        return 0

    @staticmethod
    def  test_maxiumum_test_case_fail_spinn2():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        chip_router = machine.get_chip(0, 0).router
        for index in range(1010):
            chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over"
                                             " the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0


    @staticmethod
    def test_maxiumum_test_case_success_spinn2():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        chip_router = machine.get_chip(0, 0).router
        for index in range(10):
            chip_router.ralloc(index, 0xffffffff)
        router.Router.check_for_table_supassing_maxiumum_level(machine)
        return 0

    @staticmethod
    def test_maxiumum_test_case_multiple_fail_spinn2():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        first_chip_router = machine.get_chip(0, 0).router
        second_chip_router = machine.get_chip(0, 1).router

        for index in range(1010):
            first_chip_router.ralloc(index, 0xffffffff)
            second_chip_router.ralloc(index, 0xffffffff)
        try:
            router.Router.check_for_table_supassing_maxiumum_level(machine)
            raise exceptions.SystemException("router was passed when had over "
                                             "the maxiumum level of entries")
        except exceptions.RouteTableDSGException as e:
            return 0

    @staticmethod
    def test_inconsistant_table_entry_success():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        first_chip_router = machine.get_chip(0, 0).router
        used_masks = dict()
        used_masks[0x0000000f] = list()
        for index in range(10):
            routing_entry = first_chip_router.ralloc(index, 0x0000000f)
            used_masks[0x0000000f].append(index)
            routing_entry.route = random.randint(0, 6)
        inconsistant_routings, redundant_paths = \
            router.Router.check_for_inconsistant_routings(machine, used_masks)
        assert(len(inconsistant_routings) == 0)

    @staticmethod
    def test_inconsistant_table_entry_fail_once():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        first_chip_router = machine.get_chip(0, 0).router
        used_masks = dict()
        used_masks[0x0000000f] = list()
        for index in range(10):
            routing_entry = first_chip_router.ralloc(index, 0x0000000f)
            used_masks[0x0000000f].append(index)
            routing_entry.route = 6
        #adding bad routing entry
        routing_entry = first_chip_router.ralloc(int(17), 0x0000000f)
        used_masks[0x0000000f].append(17)
        routing_entry.route = 5

        inconsistant_routings, redundant_paths = \
            router.Router.check_for_inconsistant_routings(machine, used_masks)
        assert(len(inconsistant_routings) == 0)

    @staticmethod
    def test_inconsistant_table_entry_fail_multiple():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        first_chip_router = machine.get_chip(0, 0).router
        routing_entry = first_chip_router.ralloc(18, 0x0000000f)
        routing_entry.route = 5
        for index in range(10):
            routing_entry = first_chip_router.ralloc(index, 0x0000000f)
            routing_entry.route = 6
        routing_entry = first_chip_router.ralloc(17, 0x0000000f)
        routing_entry.route = 5

        used_masks = dict()
        used_masks[0x0000000f] = list()
        used_masks[0x0000000f].append(18)
        used_masks[0x0000000f].append(17)

        inconsistant_routings, redundant_paths = \
            router.Router.check_for_inconsistant_routings(machine, used_masks)
        assert(len(inconsistant_routings) == 0)

    @staticmethod
    def test_inconsistant_table_entry_fail_multiple_masks_combined():
        machine = lib_machine.Machine('spinn-2', x=2, y=2, type="spinn2")
        first_chip_router = machine.get_chip(0, 0).router
        routing_entry = first_chip_router.ralloc(18, 0x0000000f)
        routing_entry.route = 5
        for index in range(10):
            routing_entry = first_chip_router.ralloc(index, 0x0000000f)
            routing_entry.route = 6
        routing_entry = first_chip_router.ralloc(17, 0x0000000f)
        routing_entry.route = 5

        used_masks = dict()
        used_masks[0x0000000f] = list()
        used_masks[0x0000000f].append(18)
        used_masks[0x0000000f].append(17)

        inconsistant_routings, redundant_paths = \
            router.Router.check_for_inconsistant_routings(machine, used_masks)
        assert(len(inconsistant_routings) == 0)

if __name__=="__main__":
    #unittest.main()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_fail_edge_case_spinn7()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_success_edge_case_spinn7()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_fail_spinn7()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_success_spinn7()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_multiple_fail_spinn7()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_fail_edge_case_spinn2()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_success_edge_case_spinn2()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_fail_spinn2()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_success_spinn2()
    TestRoutingConsistancyChecks.test_maxiumum_test_case_multiple_fail_spinn2()
    TestRoutingConsistancyChecks.test_inconsistant_table_entry_success()
    TestRoutingConsistancyChecks.test_inconsistant_table_entry_fail_once()
    TestRoutingConsistancyChecks.test_inconsistant_table_entry_fail_multiple()
    #TestRoutingConsistancyChecks.test_inconsistant_table_entry_fail_multiple_masks_combined()
    #exit()
