import unittest
import math
import random
import sys

from pacman103.core.mapper.router.router import Router
from pacman103.core.mapper.placer_algorithms.basic_placer import BasicPlacer as Placer
from pacman103.lib import graph, lib_map
from pacman103.lib.machine import machine
from pacman103.core.mapper.routing_algorithms import dijkstra_routing
from pacman103.front.pynn import models
from pacman103.core import dao

class TestRedundantPathRemoval(unittest.TestCase):

    #hard coded routes with two path that intersect at the destination node
    @staticmethod
    def test_redundent_paths_spinn7():
        the_machine = machine.Machine('spinn-7', type="spinn4")
        #first route
        chip_router = the_machine.chips[0][0].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        old_entry = routing_entry
        


        chip_router = the_machine.chips[0][1].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2
        old_entry = routing_entry


        chip_router = the_machine.chips[0][2].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2
        old_entry = routing_entry


        chip_router = the_machine.chips[0][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 8 # internal
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2


        #second route
        chip_router = the_machine.chips[0][0].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 1 # north east
        old_entry = routing_entry
        

        chip_router = the_machine.chips[1][1].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 1
        old_entry = routing_entry

        chip_router = the_machine.chips[1][2].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2
        old_entry = routing_entry


        chip_router = the_machine.chips[1][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 7 # west
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2
        old_entry = routing_entry


        chip_router = the_machine.chips[0][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 10 # internal
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 < 7
        old_entry = routing_entry

        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(inconsistant_routings) == 0)
        assert(len(redundant_paths) > 0)
        Router.redundant_path_removal(redundant_paths, the_machine)
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) == 0)
        assert(len(inconsistant_routings) == 0)

        assert(len(the_machine.chips[0][0].router.cam) == 1)
        assert(len(the_machine.chips[0][1].router.cam) == 1)
        assert(len(the_machine.chips[0][2].router.cam) == 1)
        assert(len(the_machine.chips[0][3].router.cam) == 1)
        assert(len(the_machine.chips[1][1].router.cam) == 0)
        assert(len(the_machine.chips[1][2].router.cam) == 0)
        assert(len(the_machine.chips[1][3].router.cam) == 0)

        assert(the_machine.chips[0][3].router.cam.get(0 & 0xffffffff)[0].route ==
               (1 << 10) + (1 << 8))
        #print bin(the_machine.chips[0][0].router.cam.get(0 & 0xffffffff)[0].route)
        #print bin(1 << 2)
        assert(the_machine.chips[0][0].router.cam.get(0 & 0xffffffff)[0].route ==
               (1 << 2))

    #test to see if 3 routes (2 going to the same destination and one which
    # does not but intersects the removed path)
    @staticmethod
    def test_redundent_paths_with_non_deletable_branch_spinn7():
        the_machine = machine.Machine('spinn-7', type="spinn4")
        #first route
        chip_router = the_machine.chips[0][0].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        old_entry = routing_entry

        chip_router = the_machine.chips[0][1].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 5
        old_entry = routing_entry

        chip_router = the_machine.chips[0][2].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 5
        old_entry = routing_entry


        chip_router = the_machine.chips[0][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 8 # internal
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 5


        #second route
        chip_router = the_machine.chips[0][0].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 1 # north east
        old_entry = routing_entry


        chip_router = the_machine.chips[1][1].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        #print bin(1 << 0)
        routing_entry.route = 5 # north and east
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 1
        old_entry = routing_entry

        chip_router = the_machine.chips[1][2].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 2 # north
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = (1 << 2)
        old_entry = routing_entry


        chip_router = the_machine.chips[1][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 7   #west
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 << 2
        old_entry = routing_entry


        chip_router = the_machine.chips[0][3].router
        routing_entry = chip_router.ralloc(0, 0xffffffff)
        routing_entry.route = 1 << 10 # internal
        routing_entry.previous_router_entry = old_entry
        routing_entry.previous_router_entry_direction = 1 < 7
        old_entry = routing_entry

        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(inconsistant_routings) == 0)
        assert(len(redundant_paths) > 0)
        Router.redundant_path_removal(redundant_paths, the_machine)
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) == 0)
        assert(len(inconsistant_routings) == 0)

        assert(len(the_machine.chips[0][0].router.cam) == 1)
        assert(len(the_machine.chips[0][1].router.cam) == 1)
        assert(len(the_machine.chips[0][2].router.cam) == 1)
        assert(len(the_machine.chips[0][3].router.cam) == 1)
        assert(len(the_machine.chips[1][1].router.cam) == 1)
        assert(len(the_machine.chips[1][2].router.cam) == 0)
        assert(len(the_machine.chips[1][3].router.cam) == 0)
        assert(the_machine.chips[0][3].router.cam.get(0 & 0xffffffff)[0].route ==
               (1 << 10) + (1 << 8))
        assert(the_machine.chips[0][0].router.cam.get(0 & 0xffffffff)[0].route == 6)

    #testing using router code base
    @staticmethod
    def test_redundant_paths_spinn7_via_router_straight_line():
        the_machine = machine.Machine('spinn-7', type="spinn4")
        src_vertex_constraints = lib_map.VertexConstraints(x=0, y=0)
        src_vrt = graph.Vertex(1,models.IF_curr_exp,
                               constraints=src_vertex_constraints)
        src_sub_vert = graph.Subvertex(src_vrt, 0,1)

        dest_vertex_constraints = lib_map.VertexConstraints(x=0, y=3)
        dest_vrt = graph.Vertex(1,models.IF_curr_exp,
                                constraints=dest_vertex_constraints)
        dest_sub_vert = graph.Subvertex(dest_vrt, 0,1)
        dest_sub_vert2 = graph.Subvertex(dest_vrt, 0,1)

        edge = graph.Edge(None, src_vrt, dest_vrt)
        sbedge = graph.Subedge(edge, src_sub_vert, dest_sub_vert)
        sbedge2 = graph.Subedge(edge, src_sub_vert, dest_sub_vert2)

        dao_object = dao
        #place vertexes in correct cores
        placements = Placer.place_raw(the_machine,
                                             [src_sub_vert, dest_sub_vert,
                                              dest_sub_vert2])
        dao.placements = placements
        routings = dijkstra_routing.DijkstraRouting.\
            route_raw(the_machine, [src_sub_vert, dest_sub_vert, dest_sub_vert2])
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) > 0)
        assert(len(inconsistant_routings) == 0)
        Router.redundant_path_removal(redundant_paths, the_machine)
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) == 0)
        assert(len(inconsistant_routings) == 0)

    #testing using router code base
    @staticmethod
    def test_redundant_paths_spinn7_via_router_require_turn():
        the_machine = machine.Machine('spinn-7', type="spinn4")
        src_vertex_constraints = lib_map.VertexConstraints(x=0, y=0)
        src_vrt = graph.Vertex(1,models.IF_curr_exp,
                               constraints=src_vertex_constraints)
        src_sub_vert = graph.Subvertex(src_vrt, 0,1)

        dest_vertex_constraints = lib_map.VertexConstraints(x=2, y=3)
        dest_vrt = graph.Vertex(1,models.IF_curr_exp,
                                constraints=dest_vertex_constraints)
        dest_sub_vert = graph.Subvertex(dest_vrt, 0,1)
        dest_sub_vert2 = graph.Subvertex(dest_vrt, 0,1)

        edge = graph.Edge(None, src_vrt, dest_vrt)
        sbedge = graph.Subedge(edge, src_sub_vert, dest_sub_vert)
        sbedge2 = graph.Subedge(edge, src_sub_vert, dest_sub_vert2)

        dao_object = dao
        #place vertexes in correct cores
        placements = Placer.place_raw(the_machine,
                                             [src_sub_vert, dest_sub_vert,
                                              dest_sub_vert2])
        dao.placements = placements
        routings = dijkstra_routing.DijkstraRouting.\
            route_raw(the_machine, [src_sub_vert, dest_sub_vert, dest_sub_vert2])
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) > 0)
        assert(len(inconsistant_routings) == 0)
        Router.redundant_path_removal(redundant_paths, the_machine)
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) == 0)
        assert(len(inconsistant_routings) == 0)



    #test using router where route is on same chip
    @staticmethod
    def test_redundant_paths_spinn7_via_router_same_chip():
        the_machine = machine.Machine('spinn-7', type="spinn4")
        src_vertex_constraints = lib_map.VertexConstraints(x=0, y=0, p=2)
        src_vrt = graph.Vertex(1, models.IF_curr_exp,
                               constraints=src_vertex_constraints)
        src_sub_vert = graph.Subvertex(src_vrt, 0,1)

        dest_vertex_constraints = lib_map.VertexConstraints(x=0, y=0, p=5)
        dest_vrt = graph.Vertex(1, models.IF_curr_exp,
                                constraints=dest_vertex_constraints)
        dest_sub_vert = graph.Subvertex(dest_vrt, 0,1)
        dest_sub_vert2 = graph.Subvertex(dest_vrt, 0,1)

        dest_vertex_constraints2 = lib_map.VertexConstraints(x=0, y=0, p=6)
        dest_vrt2 = graph.Vertex(1, models.IF_curr_exp,
                                 constraints=dest_vertex_constraints2)
        dest_sub_vert2 = graph.Subvertex(dest_vrt2, 0, 1)

        edge = graph.Edge(None, src_vrt, dest_vrt)
        sbedge = graph.Subedge(edge, src_sub_vert, dest_sub_vert)
        sbedge2 = graph.Subedge(edge, src_sub_vert, dest_sub_vert2)

        dao_object = dao
        #place vertexes in correct cores
        placements = Placer.place_raw(the_machine,
                                             [src_sub_vert, dest_sub_vert,
                                              dest_sub_vert2])
        dao.placements = placements
        routings = dijkstra_routing.\
            DijkstraRouting.route_raw(the_machine,
                                      [src_sub_vert, dest_sub_vert,
                                       dest_sub_vert2])
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) > 0)
        assert(len(inconsistant_routings) == 0)
        #print "entry {} and entry {}".format(redundant_paths[0][2].route, redundant_paths[0][3].route)
        Router.redundant_path_removal(redundant_paths, the_machine)
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(the_machine)
        assert(len(redundant_paths) == 0)
        assert(len(inconsistant_routings) == 0)
        for key in the_machine.chips[0][0].router.cam.keys():
            entry_list = the_machine.chips[0][0].router.cam.get(key)
            assert(len(entry_list) == 1)
            #print "entry is {}".format(entry_list[0].route)
            assert(entry_list[0].route == 6144)

if __name__=="__main__":
    #unittest.main()
    #TestRedundantPathRemoval.test_redundent_paths_spinn7()
    #TestRedundantPathRemoval.test_redundent_paths_with_non_deletable_branch_spinn7()
    #TestRedundantPathRemoval.test_redundant_paths_spinn7_via_router_straight_line()
    #TestRedundantPathRemoval.test_redundant_paths_spinn7_via_router_require_turn()
    TestRedundantPathRemoval.test_redundant_paths_spinn7_via_router_same_chip()
