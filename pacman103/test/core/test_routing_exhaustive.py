#!/usr/bin/env python

#alan stokes: test case to see if all possible links work with the router
# (assumes empty routing tables per test)

from pacman103.core.mapper import router
from pacman103.core.mapper.routing_algorithms import dijkstra_routing
from pacman103.lib import graph
from pacman103.lib.machine import machine
from pacman103.lib import lib_map
from pacman103.front.pynn import models
from pacman103.core import exceptions
from pacman103.core import dao
from pacman103.store import machines
import sys
import logging
import traceback
import unittest
logger = logging.getLogger(__name__)

#class ExshastiveRouteGeneration(unittest.TestCase):
class ExshastiveRouteGeneration():

    @staticmethod
    def test_four_chip_board(number_of_dests):
        '''
        checks all combinations for a 4 node board
        '''
        perms=[]
        #make permutations for placement locations.
        for x in range(2):
            for y in range(2):
                for p in range(1,17):
                    perms.append([x,y,p])
        #start testing
        '''
        source_subvert, dest_subverts, machine, subedges, fails = \
                ExshastiveRouteGeneration.try_creating_route([0,0,1], [[0,1,1],[1,0,1]], "amu12")
        fail = ExshastiveRouteGeneration.retrace_route(source_subvert, dest_subverts,
                                                                  machine, subedges)
        '''

        fails = ExshastiveRouteGeneration.explore_all_routes(perms, "amu12", number_of_dests)
        if len(fails) != 0:
            raise exceptions.PacmanException(fails)



    @staticmethod
    def test_fourty_eight_board(number_of_dests):
        '''
        checks all combinations for a 48 node board
        '''
        perms=[]
        board48gaps=[[0,4],[0,5],[0,6],[0,7],[1,5],[1,6],[1,7],[2,6],
                     [2,7],[3,7],[5,0],[6,0],[6,1],[7,0],[7,1],[7,2]]
        for x in range(8):
            for y in range(8):
                if [x,y] not in board48gaps:
                    for p in range(1,17):
                        perms.append([x,y,p])
        #start testing
        fails = ExshastiveRouteGeneration.explore_all_routes(perms, "spinn-7", number_of_dests)
        if len(fails) != 0:
            raise exceptions.PacmanException(fails)

    @staticmethod
    def explore_all_routes(perms, machine_id, number_of_dests):
        '''
        explores all routes for a combination fof desitnations
        '''
        machine = None
        failed = []
        #place two populations onto a processor in source and destination chip.
        for source in perms:
            fails_for_this_run = \
                ExshastiveRouteGeneration.recursive_generation_of_dests_and_run(perms, number_of_dests,
                                                                                list(), source, machine_id,
                                                                                failed)
            if len(fails_for_this_run) > 0:
                failed.append(fails_for_this_run)
        return failed


    @staticmethod
    def recursive_generation_of_dests_and_run(perms, number_of_dests_left_to_do,
                                              dests, source, machine_id, failed):
        '''
        selects the destinations to use in the test (exshastive)
        '''
        if number_of_dests_left_to_do == 0: # if got all dests, create route and check
            source_subvert, dest_subverts, machine, subedges, fails = \
                ExshastiveRouteGeneration.try_creating_route(source, dests, machine_id)
            if fails is not None:
                return failed.append(fails)
            else:
                fail = ExshastiveRouteGeneration.retrace_route(source_subvert, dest_subverts,
                                                                  machine, subedges)
                if len(fail) != 0:
                    failed.append(fail)

                return failed
        else:
            # need mroe dests, repeat
            for dest in perms:
                dests.append(dest)
                new_fails = ExshastiveRouteGeneration.recursive_generation_of_dests_and_run(perms, number_of_dests_left_to_do-1,
                                                                                           dests, source, machine_id, failed)
                if len(new_fails) > 0:
                    failed.append(new_fails)
                dests.remove(dest)
            return failed





    @staticmethod
    def try_creating_route(source, dests, machine_id):
        '''
        create vertexes subverts and placements, run routing, and start backward chasing
        '''
        the_machine = None
        #initilise machine
        description = machines.machines[machine_id]
        the_machine = machine.Machine(**description)
        subedges = dict()
        sub_verts = list()
        src_vertex_constraints = lib_map.VertexConstraints(x=source[0],
                                                           y=source[1],
                                                           p=source[2])
        src_vrt = models.IF_curr_exp(1, constraints=src_vertex_constraints)
        src_sub_vert = graph.Subvertex(src_vrt, 0, 1, 0)
        sub_verts.append(src_sub_vert)

        #place vertexes in correct cores
        placement_chip = the_machine.get_chip(src_sub_vert.vertex.constraints.x,
                                              src_sub_vert.vertex.constraints.y)
        placement_processor = placement_chip.get_processor(src_sub_vert.vertex.constraints.p)
        placement = lib_map.Placement(src_sub_vert, placement_processor)
        src_sub_vert.placement = placement



        #add subvert and edge for each destination vertex
        dest_subverts = list()
        for dest in dests:

            dest_vertex_constraints = lib_map.VertexConstraints(x=dest[0],
                                                                y=dest[1],
                                                                p=dest[2])
            dest_vrt = models.IF_curr_exp(1, constraints=dest_vertex_constraints)
            dest_sub_vert = graph.Subvertex(dest_vrt, 0, 1, 0)

            edge = graph.Edge(src_vrt, dest_vrt)
            sbedge = graph.Subedge(edge, src_sub_vert, dest_sub_vert)
            #give its routing key and mask
            key, mask = src_sub_vert.vertex.generate_routing_info(sbedge)
            sbedge.key = key
            sbedge.mask = mask
            sbedge.key_mask_combo = key & mask

            subedges[dest_sub_vert] = sbedge
            sub_verts.append(dest_sub_vert)
            dest_subverts.append(dest_sub_vert)
            #place vertexes in correct cores
            placement_chip = the_machine.get_chip(dest_sub_vert.vertex.constraints.x,
                                                  dest_sub_vert.vertex.constraints.y)
            placement_processor = placement_chip.get_processor(dest_sub_vert.vertex.constraints.p)
            placement = lib_map.Placement(dest_sub_vert, placement_processor)
            dest_sub_vert.placement = placement

        fails = list()

        #try to route between the verts
        try:
            dijkstra_routing.DijkstraRouting.route_raw(the_machine, sub_verts)
            return src_sub_vert, dest_subverts, machine, subedges,  None
        except Exception as e:
            print traceback.print_exc(e)
            return src_sub_vert, dest_subverts, machine, subedges, \
                   fails.append([src_sub_vert, dests, "failed to generate a route"])

    @staticmethod
    def retrace_route(src_sub_vert, dest_subverts, the_machine, subedges):

        fails = list()
        dest = None
        try:
            #retrace the route from the source via routing entries
            for dest in dest_subverts:
                successful = \
                    ExshastiveRouteGeneration.retrace_via_routing_entries(the_machine, src_sub_vert,
                                                                          dest, subedges[dest])
                if not successful:
                    fails.append([src_sub_vert, dest, "failed to locate dstination with route"])
                else:
                    logger.debug("successful test between {} and {}".format(src_sub_vert, dest))

            return fails
        except Exception as e:
            print traceback.print_exc(e)
            fails.append([src_sub_vert, dest, e.message])
            if dest_subverts.index(dest)+1 == len(dest_subverts):
                return fails
            else:
                left_over_dests= dest_subverts[dest_subverts.index(dest)+1:len(dest_subverts)]
                return ExshastiveRouteGeneration.retrace_route(src_sub_vert, left_over_dests,
                                                               the_machine, subedges)





    @staticmethod
    def retrace_via_routing_entries(the_machine, src_sub_vert, dest_sub_vert, sbedge):
        '''
        tries to retrace from the source to all dests and sees if one of them is the dest subvert
        '''
        dest_position = None
        true_dest_position = [dest_sub_vert.placement.processor.chip.x,
                              dest_sub_vert.placement.processor.chip.y,
                              dest_sub_vert.placement.processor.idx]
        no_more_entries_to_trace = False
        current_router = src_sub_vert.placement.processor.chip.router
        #get src router
        entry = ExshastiveRouteGeneration.locate_routing_entry(current_router, sbedge)
        route_value = entry.route
        found = ExshastiveRouteGeneration.trace_to_dests(route_value, dest_sub_vert, current_router,
                                                         sbedge)
        if not found:
            return 0
        else:
            return 1


    # locates the next dest pos to check
    @staticmethod
    def trace_to_dests(route_value, dest_sub_vert, current_router, sbedge):
        found = False
        #determine where the route takes us
        chip_links = ExshastiveRouteGeneration.in_chip_scope(route_value)
        processor_values = ExshastiveRouteGeneration.processor_value(route_value)
        if chip_links is not None:#if goes downa chip link
            if processor_values is not None: # also goes to a processor
                found = ExshastiveRouteGeneration.check_processor(dest_sub_vert,
                                                                  processor_values,
                                                                  current_router)
            else:#only goes to new chip
                for link_id in chip_links:
                    #locate next chips router
                    next_router = current_router.neighbourlist[link_id]['object']
                    entry = ExshastiveRouteGeneration.locate_routing_entry(next_router, sbedge)
                    route_value = entry.route # get next route value from the new router
                    if ExshastiveRouteGeneration.trace_to_dests(route_value, dest_sub_vert,
                                                                     next_router, sbedge):
                    #checks if the new route eventually finds the correct chip
                        return True
        elif processor_values is not None: #only goes to a processor
            found = ExshastiveRouteGeneration.check_processor(dest_sub_vert,
                                                              processor_values,
                                                              current_router)


        return found

    @staticmethod
    def check_processor(dest_sub_vert, processor_ids, current_router):
        dest_position = [dest_sub_vert.placement.processor.chip.x,
                         dest_sub_vert.placement.processor.chip.y,
                         dest_sub_vert.placement.processor.idx]

        if (current_router.chip.x == dest_sub_vert.placement.processor.chip.x and
            current_router.chip.y == dest_sub_vert.placement.processor.chip.y):
            #in correct chip
            for processor_id in processor_ids:
                if processor_id == dest_sub_vert.placement.processor.idx:
                    return True
        return False

    @staticmethod
    def in_chip_scope(route_value):
        '''
        returns a chip link or none based on if the route value travels down a spinn link
        '''
        link_ids = list()
        masked_off_values = route_value & 0x3F
        if masked_off_values == 0:
            return None
        else:
            masks = [0x1, 0x2, 0x4, 0x8, 0x10, 0x20]
            link_id = 0
            for mask in masks:
                final_mask_value = (masked_off_values & mask) >> link_id
                if final_mask_value == 1:
                    link_ids.append(link_id)
                link_id += 1

            return link_ids

    #
    @staticmethod
    def processor_value(route_value):

        '''
        returns a processor vlaue or None based on if the route value contains a processor point
        '''
        processor_ids = list()
        masked_off_values = route_value & 0x7FFFC0
        if masked_off_values == 0:
            return None
        else:
            masks = [0x40, 0x80, 0x100, 0x200, 0x400, 0x800, 0x1000, 0x2000,
                     0x4000, 0x8000, 0x10000, 0x20000, 0x40000, 0x80000,
                     0x100000, 0x200000, 0x400000, 0x800000]
            processor_id = 0
            for mask in masks:
                final_mask_value = masked_off_values & mask
                if final_mask_value != 0:
                    processor_ids.append(processor_id)
                processor_id += 1
            return processor_ids

    @staticmethod
    def locate_routing_entry(src_router, sbedge):
        '''
        loate the entry from the router based off the subedge
        '''
        key_combo = sbedge.key_mask_combo
        if key_combo in src_router.cam.keys():
            return src_router.cam[key_combo][0]
        else:
            raise exceptions.RouterException("no key located")


if __name__=="__main__":
    #unittest.main()
    #ExshastiveRouteGeneration.test_fourty_eight_board(2)
    ExshastiveRouteGeneration.test_four_chip_board(2)
    #exit()
