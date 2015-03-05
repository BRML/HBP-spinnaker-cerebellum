#!/usr/bin/env python

"""
Sergio Davies 31-05-2013
The current version of this test is incomplete, and therefore does not work as is.
I'm currently working on it, please do not delete this file!

export PYTHONPATH=$PYTHONPATH:/home/visitor2012/choyp/Desktop/svnStuff/pacman103
"""

import unittest
import math
import random
from pacman103.core.mapper.placer_algorithms import radial_placer

from pacman103.core.mapper.routing_algorithms import dijkstra_routing
from pacman103.lib import graph
from pacman103.lib.machine import machine
from pacman103.front.pynn import models


#the following parameter defines the number of connections
#between vertexes mapped on the machine. A value of 1 is equivalent to an
#all-to-all connectivity scheme. lower percentages define the amount of the
#all-to-all connectivity on which the routing algorithm should be tested
#this parameter influences only the test "test_routing"
test_connectivity_percentage = 0.0001

class RoutingTestCase(unittest.TestCase):
    """
    TODO
    """
    def test_routing_simple(self):
        #print "test_routing simple"
        the_machine = machine.Machine('host', type="spinn4")

        src_vrt = graph.Vertex(1, None)
        src_vrt.model = models.IF_curr_exp
        dst_vrt = graph.Vertex(1, None)
        dst_vrt.model = models.IF_curr_exp
        edge = graph.Edge(src_vrt, dst_vrt)

        src_sbvrt = graph.Subvertex(src_vrt, 0, 0, None)
        dst_sbvrt = graph.Subvertex(dst_vrt, 0, 0, None)
        sbedge = graph.Subedge(edge, src_sbvrt, dst_sbvrt)

        radial_placer = radial_placer.RadialPlacer(None)
        radial_placer.RadialPlacer.place_raw(the_machine, [src_sbvrt, dst_sbvrt])

        dijkstra_routing.DijkstraRouting.route_raw(the_machine, [src_sbvrt,
                                                                 dst_sbvrt])
        #the machine object now contains all the routes
        #now I need to test that the routes are correct
        #(i.e. from a single source they go to the correct destination(s))

        out_sbedges_lst = src_sbvrt.out_subedges

        #the routing key dictionary associates to a routing key the list of
        #destinations
        rt_key_list = dict()

        for i in range(len(out_sbedges_lst)):

            #for each subvertex and for each subedge key and mask are retrieved
            key, mask = src_sbvrt.vertex.model.generate_routing_info(out_sbedges_lst[i])

            #then the destination of the subedge is retrieved
            dst = out_sbedges_lst[i].postsubvertex.placement.processor.get_coordinates()

            #and it is added to the appropriate list
            #then all the destinations are merged in the list rt_key_list
            if key in rt_key_list:
                #if the routing key for the subedge is already in the rt_key_list
                #then append the destination to the list of the destinations
                #extracted from the graph
                if dst not in rt_key_list[key]:
                    rt_key_list[key].append(dst)
            else:
                #if the routing key was not present in the lsit of already known
                #routing keys, then append it with the new destination
                rt_key_list.update({key:[dst]})



            #rt_key list at this point is a dictionary of elements; each of these
            #elements contains a list where the elements are destinations

            #{'key1':[dst1, dst2, ...], 'key2':[dst3, dst4, ...], ...}

        for i in range(len(rt_key_list.keys())):
            #retrieve the list of desired destinations from rt_key_list
            key = rt_key_list.keys()[i]
            desired_dsts = rt_key_list[key]
            #sort destinations
            desired_dsts.sort()

            #get from the binaries of the routing tables the destination core(s)
            #for a specific routing key starting from a particular chip
            test = TestRoutes (the_machine, src_sbvrt, key)
            test.TraceRoute()
            dsts = test.dsts
            dsts.sort()
            #dsts contains the list of processors to which the routing key is
            #addresses. this list must be equal to the desired destination(s)
            #extracted from the graph

            #test desired_dsts and dsts. if not equal, the routing made a mess!
            #print "desired_dsts: ", desired_dsts
            #print "dsts: ",dsts
            self.assertEqual (dsts, desired_dsts)


    def test_routing(self):

        the_machine = machine.Machine('host', type="spinn4")

        machine_size = len(the_machine.processors)
        vertexes = list()

        for i in xrange(machine_size):
            v = graph.Vertex(1, None)
            v.model = models.IF_curr_exp
            vertexes.append(v)

        number_of_projections = machine_size * machine_size * test_connectivity_percentage
        src_vertexes = random.sample(xrange(machine_size), int(math.ceil(math.sqrt(number_of_projections))))
        dst_vertexes = random.sample(xrange(machine_size), int(math.floor(math.sqrt(number_of_projections))))

        src_vertexes.sort()
        dst_vertexes.sort()

#        print "test_routing: total number of projections:", number_of_projections
#        print "test_routing: source vertexes", src_vertexes
#        print "test_routing: destination vertexes:", dst_vertexes
#        print "test_routing: number of projections:", len(src_vertexes) * len(dst_vertexes)

        edges = list()
        for i in xrange(len(src_vertexes)):
            for j in xrange(len(dst_vertexes)):
                src = vertexes[src_vertexes[i]]
                dst = vertexes[src_vertexes[j]]
                edges.append(graph.Edge( src, dst))

        subvertexes = list()
        for i in xrange(machine_size):
            subvertexes.append(graph.Subvertex(vertexes[i], 0, 0, None))

        sb_edges = list()
        for i in xrange(len(edges)):
            pre = edges[i].prevertex.subvertices[0]
            post = edges[i].postvertex.subvertices[0]
            sb_edges.append(graph.Subedge(edges[i], pre, post))

        radial_placer.RadialPlacer.place_raw(the_machine, subvertexes)

        dijkstra_routing.DijkstraRouting.route_raw(the_machine, subvertexes)
        #the machine object now contains all the routes
        #now I need to test that the routes are correct
        #(i.e. from a single source they go to the correct destination(s))

        for k in xrange(len(src_vertexes)):
            #take the list of the outgoing edges from each of the subvertexes
            src_sbvrt = subvertexes[src_vertexes[k]]
            out_sbedges_lst = src_sbvrt.out_subedges

            #the routing key dictionary associates to a routing key the list of
            #destinations
            rt_key_list = dict()

            for i in range(len(out_sbedges_lst)):

                #for each subvertex and for each subedge key and mask are retrieved
                key, mask = src_sbvrt.vertex.model.generate_routing_info(out_sbedges_lst[i])

                #then the destination of the subedge is retrieved
                dst = out_sbedges_lst[i].postsubvertex.placement.processor.get_coordinates()

                #and it is added to the appropriate list
                #then all the destinations are merged in the list rt_key_list
                if key in rt_key_list:
                    #if the routing key for the subedge is already in the rt_key_list
                    #then append the destination to the list of the destinations
                    #extracted from the graph
                    if dst not in rt_key_list[key]:
                        rt_key_list[key].append(dst)
                else:
                    #if the routing key was not present in the lsit of already known
                    #routing keys, then append it with the new destination
                    rt_key_list.update({key:[dst]})

                #rt_key list at this point is a dictionary of elements; each of these
                #elements contains a list where the elements are destinations

                #{'key1':[dst1, dst2, ...], 'key2':[dst3, dst4, ...], ...}

            for i in range(len(rt_key_list.keys())):
                #retrieve the list of desired destinations from rt_key_list
                key = rt_key_list.keys()[i]
                desired_dsts = rt_key_list[key]
                #sort destinations
                desired_dsts.sort()
                #print "Desired destinations:", desired_dsts

                #get from the binaries of the routing tables the destination core(s)
                #for a specific routing key starting from a particular chip
                test = TestRoutes (the_machine, src_sbvrt, key)
                test.TraceRoute()
                dsts = test.dsts
                dsts.sort()
                #print "Actual destinations:", dsts
                #dsts contains the list of processors to which the routing key is
                #addresses. this list must be equal to the desired destination(s)
                #extracted from the graph

                #test desired_dsts and dsts. if not equal, the routing made a mess!
                self.assertEqual (dsts, desired_dsts)

class TestRoutes:
    """
    TODO
    """
    def __init__(self, machine, src_vertex, rt_key):
        """
        TODO
        """
        self.dsts = list()
        self.machine = machine
        self.src_vertex = src_vertex
        self.rt_key = rt_key

    def TraceRoute(self):
        """
        TODO
        """
        x, y, p = self.src_vertex.placement.processor.get_coordinates()
        self.TraceRouteRaw (x, y)

        return self.dsts

    def TraceRouteRaw(self, x, y):
        """
        TODO
        """
        machine_x_size = self.machine.x_dim
        machine_y_size = self.machine.y_dim

        routing_table = self.machine.chips[x][y].router.cam

        #the following is a list of elements "RoutingEntry"
        destinations = routing_table[self.rt_key]

        for i in range(len(destinations)):
            if destinations[i].route & 0x1: #direction West
                next_x = (x+1) % machine_x_size
                next_y = y
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x2: #direction North-West
                next_x = (x+1) % machine_x_size
                next_y = (y+1) % machine_y_size
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x4: #direction North
                next_x = x
                next_y = (y+1) % machine_y_size
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x8: #direction East
                next_x = (x-1) % machine_x_size
                next_y = y
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x10: #direction South-East
                next_x = (x-1) % machine_x_size
                next_y = (y-1) % machine_y_size
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x20: #direction South
                next_x = x
                next_y = (y-1) % machine_y_size
                self.TraceRouteRaw(next_x, next_y)
            elif destinations[i].route & 0x40: #delivered to core 0
                dest = (x, y, 0)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x80: #delivered to core 1
                dest = (x, y, 1)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x100: #delivered to core 2
                dest = (x, y, 2)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x200: #delivered to core 3
                dest = (x, y, 3)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x400: #delivered to core 4
                dest = (x, y, 4)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x800: #delivered to core 5
                dest = (x, y, 5)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x1000: #delivered to core 6
                dest = (x, y, 6)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x2000: #delivered to core 7
                dest = (x, y, 7)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x4000: #delivered to core 8
                dest = (x, y, 8)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x8000: #delivered to core 9
                dest = (x, y, 9)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x10000: #delivered to core 10
                dest = (x, y, 10)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x20000: #delivered to core 11
                dest = (x, y, 11)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x40000: #delivered to core 12
                dest = (x, y, 12)
                if dest not in self.dsts:
                    self.dsts.append(dest)
                dest = (x, y, 13)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x100000: #delivered to core 14
                dest = (x, y, 14)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x200000: #delivered to core 15
                dest = (x, y, 15)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x400000: #delivered to core 16
                dest = (x, y, 16)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            elif destinations[i].route & 0x800000: #delivered to core 17
                dest = (x, y, 17)
                if dest not in self.dsts:
                    self.dsts.append(dest)
            else:
                self.assertTrue(False, "Unknown route destination!")

        #print len(destinations)
        #print "destinations: ",destinations
        #print "destinations: ",hex(destinations)


if __name__=="__main__":
    unittest.main()
