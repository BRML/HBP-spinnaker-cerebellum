__author__ = 'stokesa6'

from pacman103.lib import lib_map as lib_map
from pacman103.core.utilities import router_util as util
from pacman103.lib.machine.router import Router
import logging
import os
from pacman103.core import reports

from pacman103 import conf
logger = logging.getLogger( __name__ )

class SteinerTreeWeightedRouting(object):

    # There are more if statements than are necessary, but the code is more easily interpreted like this.
    # 'direction' is the direction in which you travelled to get from xold, yold to xnew, ynew
    # The direction is a 6 bit string with one '1' entry.

    #ABS this method has been modified to take into account the wrapping of the boards when giving directions.
    # it assumes that the neighbours are positioned in the following pattern for its index in the neighbourhood list. E,NE,N,W,SW,S
    # to remove this assumption would require knwoeldge of which links are wraparounds.
    @staticmethod
    def get_direction(neighbour_position):
        direction = None
        if neighbour_position == 0:
            bin_direction = 1 << 3  # East
            dec_direction = 3
        elif neighbour_position == 1:
            bin_direction = 1 << 4  # North East
            dec_direction = 4
        elif neighbour_position == 2:
            bin_direction = 1 << 5  # North
            dec_direction = 5
        elif neighbour_position == 3:
            bin_direction = 1 << 0  # West
            dec_direction = 0
        elif neighbour_position == 4:
            bin_direction = 1 << 1  # South West
            dec_direction = 1
        elif neighbour_position == 5:
            bin_direction = 1 << 2  # South
            dec_direction = 2
        return bin_direction, dec_direction


    # Returns the 'weight' of the arc as a function of the node and arc info
    # The weight should be some function of the path length (obviously), the remaining bandwidth along that link,
    # and the remaining free entries in the routing table.
    # Currently I am using a reciprocal function, however there is a large choice of functions with varying smoothness to be considered.
    # Of particular interest is a log function which exhibits a much greater smoothness: however it was my intuition that the steeper reciprocal function would
    # work better.
    # Also, in both 'Q' and 'T', there is a term which subtracts the value of the reciprocal function when none of the resource has been used. This
    # has the effect of making the cost start at exactly zero.#
    # Both Q and T reach infinity smoothly when the resource is used fully.
    @staticmethod
    def get_weight(post_router, bw, l, m, k, MAX_BW):

        #locate the number of defaultables
        defaultables = 0
        for entry_key in post_router.cam.keys():
            entry = post_router.cam[entry_key]
            if entry.defaultable:
                defaultables += 1

        free_entries = (post_router.MAX_OCCUPANCY -
                       (post_router.occupancy - defaultables))

        Q = float(l * (1 / float(free_entries) - 1 / float(post_router.MAX_OCCUPANCY))) #weight based off entries left

        T = m * (1 / float(bw) - 1 / float(MAX_BW)) # weight based of bandwidth

        weight = k + Q + T

        return weight

    @staticmethod
    def reset_tables(dijkstra_tables):

        for key in dijkstra_tables.keys():
            dijkstra_tables[key]["lowest cost"] = None
            dijkstra_tables[key]["activated?"] = False


    @staticmethod
    def update_weights(nodes_info, machine, l, m, k, MAX_BW):
        for key in nodes_info.keys():
            if nodes_info[key] is not None:
                for n in range(len(nodes_info[key]["neighbours"])):
                    if nodes_info[key]["neighbours"][n] is not None:
                        neighbour = nodes_info[key]["neighbours"][n]
                        xn, yn = neighbour["x"], neighbour["y"]
                        nodes_info[key]["weights"][n] = \
                            SteinerTreeWeightedRouting.get_weight(machine.get_chip(xn, yn).router,
                                                       nodes_info[key]["bws"][n],
                                                       l, m, k, MAX_BW)


    @staticmethod
    def properate_costs_till_reached_destinations(dijkstra_tables, nodes_info,
                                                 xa, ya, destination_processors,
                                                 xs, ys):
        destination_processors_left_to_find = destination_processors
        # Iterate only if the destination node hasn't been activated
        while not (len(destination_processors_left_to_find) == 0):

            # PROPAGATE!
            for i in range(len(nodes_info["{}:{}".format(xa, ya)]["neighbours"])):

                neighbour = nodes_info["{}:{}".format(xa, ya)]["neighbours"][i]
                link = nodes_info["{}:{}".format(xa, ya)]["bws"][i]
                weight = nodes_info["{}:{}".format(xa, ya)]["weights"][i]

                # "neighbours" is a list of 6 dictionaries or None objects.
                # There is a None object where there is no connection to that neighbour.
                if (neighbour is not None) and not (neighbour["x"] == xs and neighbour["y"] == ys):

                    # These variables change with every look at a new neighbour
                    xn, yn = neighbour["x"], neighbour["y"]

                    # Only try to update if the neighbour is within the graph
                    if "{}:{}".format(xn, yn) in dijkstra_tables.keys():
                        # Only update the cost if the node hasn't already been activated
                        if (dijkstra_tables["{}:{}".format(xn, yn)]["activated?"] == False):

                            # Only update the lowest cost if the new cost is less, or if there is no current cost
                            if ((dijkstra_tables["{}:{}".format(xa, ya)]["lowest cost"] + weight) < dijkstra_tables["{}:{}".format(xn, yn)]["lowest cost"]
                            or (dijkstra_tables["{}:{}".format(xn, yn)]["lowest cost"] == None)):

                                dijkstra_tables["{}:{}".format(xn, yn)]["lowest cost"] = float(dijkstra_tables["{}:{}".format(xa, ya)]["lowest cost"] + weight)

                    else:
                        raise Exception("Tried to propagate to (%d, %d), which is not in the graph: "
                                        "remove non-existent neighbours") % (xn, yn)

                    if (dijkstra_tables["{}:{}".format(xn, yn)]["lowest cost"] == 0) and (xn != xs or yn != ys):
                        raise Exception("!!!Cost of non-source node (%s, %s) was set to zero!!!") % (xn, yn)

            # This cannot be done in the above loop, since when a node becomes activated
            # the rest of the costs cannot be retrieved, and a new graph lowest cost cannot be found
            graph_lowest_cost = None  # This is the lowest cost across ALL unactivated nodes in the graph.

            # Find the next node to be activated
            for key in dijkstra_tables.keys():
                # Don't continue if the node hasn't even been touched yet
                if not (dijkstra_tables[key]["lowest cost"] is None):

                    # An activated node can't be activated again
                    if (dijkstra_tables[key]["activated?"] is False):

                        if ((dijkstra_tables[key]["lowest cost"] < graph_lowest_cost and graph_lowest_cost != None)
                        or (graph_lowest_cost == None)):

                            graph_lowest_cost = dijkstra_tables[key]["lowest cost"]
                            bits = key.split(":")
                            xa, ya = int(bits[0]), int(bits[1])  # Set the next activated node as the unactivated node with the lowest current cost

            dijkstra_tables["{}:{}".format(xa, ya)]["activated?"] = True

            # If there were no unactivated nodes with costs, but the destination was not reached this iteration, raise an exception
            if (graph_lowest_cost is None):
                break
                raise Exception("Destination could not be activated, ending run")

            #check if each destination node left to find has been activated
            for dest_processor in destination_processors:
                xd, yd, pd = dest_processor.get_coordinates()
                if dijkstra_tables["{}:{}".format(xd, yd)]["activated?"]:
                    destination_processors_left_to_find.remove(dest_processor)


    #sets up the node info data structure
    @staticmethod
    def initiate_node_info(machine, MAX_BW):
        nodes_info = dict()
        for coord in machine.get_coords_of_all_chips():
            x, y = coord['x'], coord['y']
            # get_neighbours should return a list of
            # dictionaries of 'x' and 'y' values
            nodes_info["{}:{}".format(x, y)] = dict()
            nodes_info["{}:{}".format(x, y)]["neighbours"] = \
                machine.get_chip(x, y).router.get_neighbours()

            nodes_info["{}:{}".format(x, y)]["bws"] = []

            nodes_info["{}:{}".format(x, y)]["weights"] = []

            for i in range(len(nodes_info["{}:{}".format(x, y)]["neighbours"])):

                nodes_info["{}:{}".format(x, y)]["weights"].append(None)

                if nodes_info["{}:{}".format(x, y)]["neighbours"][i] is None:

                    nodes_info["{}:{}".format(x, y)]["bws"].append(None)

                else:

                    nodes_info["{}:{}".format(x, y)]["bws"].append(MAX_BW)

            logger.debug( "({}, {}) has neighbours:".format(x, y) )

            for neighbour in nodes_info["{}:{}".format(x, y)]["neighbours"]:
                if neighbour is not None:
                    logger.debug("%d, %d" % (neighbour["x"], neighbour["y"]))
                else:
                    logger.debug(neighbour)
        return nodes_info

    # sets up the initial dijkstra tables
    @staticmethod
    def initiate_dijkstra_tables(machine):
        dijkstra_tables = dict()  # Holds all the information about nodes within one full run of Dijkstra's algorithm

        for coord in machine.get_coords_of_all_chips():
            x, y = coord['x'], coord['y']
            dijkstra_tables["{}:{}".format(x, y)] = dict()# Each node has a dictionary, or 'table'

            dijkstra_tables["{}:{}".format(x, y)]["lowest cost"] = None
            dijkstra_tables["{}:{}".format(x, y)]["activated?"] = False
        return dijkstra_tables

    # takes the dijkstra table and traces back from the destination though lower costs till it reaches the source
    @staticmethod
    def retrace_back_to_source(xd, yd, machine, nodes_info, dijkstra_tables,
                               key, mask, key_combo, routing, pd,
                               BW_PER_ROUTE_ENTRY):
        # Set the tracking node to the destination to begin with
        xt, yt = xd, yd
        new_routing_entry = machine.get_chip(xd, yd).router.ralloc(key, mask)
        if new_routing_entry is None:
            raise Exception('Routing-table entry allocation failed.')
        new_routing_entry.route = 1 << (6 + pd)  # I really have no idea why pd is there
        new_routing_entry.routing = routing
        #check that the key hasnt already been used
        length = len(machine.get_chip(xd, yd).router.cam[key_combo])
        if len(machine.get_chip(xd, yd).router.cam[key_combo]) >= 2:
            other_entry = machine.get_chip(xd, yd).router.cam[key_combo][0]
            if other_entry.original_key == key:
                #merge routes
                old_route = other_entry.route
                other_entry.route += new_routing_entry.route
                #add the other routing entry to the current list
                routing.routing_entries.append(other_entry)
                if (new_routing_entry.route == old_route and
                    other_entry.previous_router_entry is not None):
                    other_entry.defaultable = True
                else:
                    other_entry.defaultable = False

            machine.get_chip(xd, yd).router.cam[key_combo].remove(new_routing_entry)
            machine.get_chip(xd, yd).router.occupancy -= 1

        else:
            routing.routing_entries.append(new_routing_entry)

        #print ("Destination occupancy is %d") % machine.chips[xd][yd].router.occupancy

        while (dijkstra_tables["{}:{}".format(xt, yt)]["lowest cost"] != 0):

            xcheck, ycheck = xt, yt

            for n in range(len(nodes_info["{}:{}".format(xt, yt)]["neighbours"])):
                neighbour = nodes_info["{}:{}".format(xt, yt)]["neighbours"][n]

                # "neighbours" is a list of 6 dictionaries or None objects. There is a None object where there is no connection to that neighbour.
                if  (neighbour != None):

                    # xnr and ynr for 'x neighbour retrace', 'y neighbour retrace'.
                    xnr, ynr = neighbour["x"], neighbour["y"]

                    # Only check if it can be a preceding node if it actually exists
                    if "{}:{}".format(xnr, ynr) in dijkstra_tables.keys():

                        if (dijkstra_tables["{}:{}".format(xnr, ynr)]["lowest cost"] != None):

                            # Set the direction of the routing entry as that which is from the preceding node to the current tracking node
                            # xnr, ynr are the 'old' coordinates since they are from the preceding node.
                            # xt and yt are the 'new' coordinates since they are where the router should send the packet to
                            binDirection, decDirection = SteinerTreeWeightedRouting.get_direction(n)

                            weight = nodes_info["{}:{}".format(xnr, ynr)]["weights"][decDirection]

                            sought_cost = dijkstra_tables["{}:{}".format(xt, yt)]["lowest cost"] - weight
                            #print ("Checking node (%d, %d) with sought cost %s and actual cost %s") % (xnr, ynr, sought_cost, dijkstra_tables[xnr][ynr]["lowest cost"])

                            if abs(dijkstra_tables["{}:{}".format(xnr, ynr)]["lowest cost"] - sought_cost) < 0.00000000001: # TODO this may be too precise! However, making it less precise could break the code.
                                if key_combo in machine.get_chip(xnr, ynr).router.cam:
                                    #already has an entry, check if mergable, if not then throw error,
                                    # therefore should only ever have 1 entry
                                    other_entry = machine.get_chip(xnr, ynr).router.cam[key_combo][0]
                                    if other_entry.original_key == key:
                                        #merge routes
                                        old_route = other_entry.route
                                        other_entry.route |= binDirection
                                        #add the other routing entry to the current list
                                        routing.routing_entries.append(other_entry)
                                        if (other_entry.route == old_route and
                                            other_entry.previous_router_entry is not None and
                                            len(routing.routing_entries) > 0 and
                                            other_entry.previous_router_entry == routing.routing_entries[0]):
                                            other_entry.defaultable = True
                                        else:
                                            other_entry.defaultable = False
                                else:
                                    # Create a routing entry on the preceding node
                                    new_routing_entry = machine.get_chip(xnr, ynr).router.ralloc(key, mask)

                                    if new_routing_entry is None:
                                        raise Exception('Routing-table entry allocation failed. Ran out of routing entry tables.')

                                    new_routing_entry.route = binDirection

                                    # Set the reference to the parent routing
                                    new_routing_entry.routing = routing

                                    # Prepend the routing entry to routing_entries
                                    routing.routing_entries.insert(0, new_routing_entry)

                                    # If this routing entry has the same direction as the one after it in the routing(remember we are tracing backwards),
                                    # then make the routing entry after this one 'default eligible'.
                                    if (len(routing.routing_entries) >= 0 and
                                        routing.routing_entries[1].route == routing.routing_entries[0].route and
                                        other_entry.previous_router_entry is not None and
                                        other_entry.previous_router_entry == routing.routing_entries[0]):
                                        routing.routing_entries[1].defaultable = True

                                    routing.routing_entries[0].previous_router_entry = routing.routing_entries[1]
                                    routing.routing_entries[0].previous_router_entry_direction = routing.routing_entries[1].route
                                    routing.routing_entries[1].next_router_entries.append(routing.routing_entries[0])


                                # Finally move the tracking node
                                xt, yt = xnr, ynr

                                #print ("Traced back to (%d, %d), forward direction was %s") % (xnr, ynr, bin(new_routing_entry.route))

                                nodes_info["{}:{}".format(xnr, ynr)]["bws"][decDirection] -= BW_PER_ROUTE_ENTRY  # TODO arbitrary

                                if (nodes_info["{}:{}".format(xnr, ynr)]["bws"][decDirection] < 0):

                                    print ("Bandwidth overused from (%d, %d) in direction %s! to (%d, %d)") % (xnr, ynr, binDirection, xt, yt)

                                    raise Exception("Bandwidth overused as described above! Terminating...")

                                # !!! IMPORTANT !!! loop must be broken, otherwise false routing entries can be made
                                break

                    else:

                        print xnr, ynr

                        raise Exception("Tried to trace back to node not in graph: remove non-existent neighbours")

            if xt == xcheck and yt == ycheck:

                raise Exception("Iterated through all neighbours of tracking node but did not find a preceding node! "
                                "Consider increasing acceptable discrepancy between sought traceback cost and "
                                "actual cost at node. Terminating...")
        return xt, yt


    #prints out helpful route info
    @staticmethod
    def printRoute(xt, yt, xs, ys, dijkstra_tables, routing):
        #if not ((xt == xs) and (yt == ys)) and dijkstra_tables[xt][yt]["lowest cost"] == 0:
         #   print Exception("Tracker reached zero, but tracking node is not source!")

        #print ("Finished retrace, final route is: "),
        output = ""
        for i in range(len(routing.routing_entries)):

            direction = routing.routing_entries[i].route

            if direction == 1:
                output += "E  "

            elif direction == 2:
                output += "NE "

            elif direction == 4:
                output +="N  "

            elif direction == 8:
                output += "W  "

            elif direction == 16:
                output += "SW "

            elif direction == 32:
                output +="S  "
        return output
       # print("")

      #  print ("Default eligible routing entries: "),

       # for i in range(len(routing.routing_entries)):

           # if routing.routing_entries[i].defaultable is True:
           #     print("1  "),

           # else:
               # print("0  "),

      #  print("")

    #raw routing method. entrance to the routing code.
    @staticmethod
    def route_raw(machine, sub_vertexes, k=1, l=0, m=0, BW_PER_ROUTE_ENTRY=0.01, MAX_BW = 250, dao=None):

        """
        Modified by peter.choy 06.08.13

        Generates a list of routings for subedges in a machine...

        For the purposes of this algorithm, we are viewing the chips as 'nodes' on a graph.
        The weight of the arcs is a function of the number of routing table entries,
        the arc length, and the remaining bandwidth along the arc's corresponding
        connection.

        The inner function of the algorithm is a slightly modified Dijkstra's algorithm.
        The outer loop loops over the necessary sub edges, and re-iterates over each
        sub edge several times. Repeating Dijkstra's algorithm for each sub edge is greedy,
        and so the iterative process may or may not be necessary.

        :param `pacman103.lib.lib_machine.Machine` machine:
            machine from which to allocate processors.
        :param list subedges:
            list of :py:class:`pacman103.lib.graph.Subedge` instances to
            route across the machine.
        :param k:
            constant that is added to arc weights to represent path length
        :param l:
            constant controlling contribution of Q to total arc weights
        :param m:
            constant controlling contribution of T to total arc weights
        :returns:
            list of :py:class:`pacman103.lib.lib_map.Routing` instances.
        """

        #print("")
        #print("Starting stopwatch...")
        #start_time = clock()

        #print("")
        #print("Initialising routing data structures...")
        routings = []

        nodes_info = SteinerTreeWeightedRouting.initiate_node_info(machine, MAX_BW)
        dijkstra_tables = SteinerTreeWeightedRouting.initiate_dijkstra_tables(machine)
        #print("")
        #print("Starting routing...")
        #print("")

        SteinerTreeWeightedRouting.update_weights(nodes_info, machine, l, m, k, MAX_BW)

        run_num = 0
        pruned_sub_edges = 0
        edge_considered = 0
        #each subsertex represents a core in the board
        for subVertex in sub_vertexes:
            subedges = subVertex.out_subedges
            
            #locate all destination and soruce coords
            dest_processors = []
            subedges_to_route = list()
            xs, ys, ps = subVertex.placement.processor.get_coordinates()
            for subedge in subedges:
                if not subedge.pruneable:
                    dest_processors.append(
                            subedge.postsubvertex.placement.processor)
                    subedges_to_route.append(subedge)
                else:
                    pruned_sub_edges += 1
            
            if(len(dest_processors) != 0):

                # Update the weights according to the changes in routing
                # tables and available bandwidth
                logger.debug("updating weights")
                SteinerTreeWeightedRouting.update_weights(nodes_info, machine,
                                                   l, m, k, MAX_BW)

                # Reset the temporary storage of lowest cost
                SteinerTreeWeightedRouting.reset_tables(dijkstra_tables)

                # SD Commented this out 20/1/14, to avoid extraneous printing
                # AS intergrated this into logger.debug
                logger.debug("***************************************************")
                logger.debug("Source node is ({}, {})".format(xs, ys))
                logger.debug("Destination nodes are(")
                for processor in dest_processors:
                    xd, yd, pd = processor.get_coordinates()
                    logger.debug("({}, {}, {})".format(xd, yd, pd))
                logger.debug("")


                # Set the first activated node in this run as the source
                xa, ya = xs, ys
                dijkstra_tables["{}:{}".format(xa, ya)]["activated?"] = True
                dijkstra_tables["{}:{}".format(xa, ya)]["lowest cost"] = 0
                # The cost at the source node is zero for obvious reasons.
                # Note that it is NOT 'None'

                SteinerTreeWeightedRouting.\
                    properate_costs_till_reached_destinations(dijkstra_tables,
                                                              nodes_info,
                                                              xa, ya,
                                                              dest_processors,
                                                              xs, ys)

                logger.debug("Reached destination from source, retracing.")
                #helpful output data
                if conf.config.getboolean( "Routing", "generate_graphs" ) and \
                    dao is not None: # AM
                    output_folder = dao.get_reports_directory("routing_graphs")
                    router_utility= util.RouterUtil(new_output_folder=output_folder)
                    router_utility.output_routing_weight(router_utility,
                                                         dijkstra_tables, machine,
                                                         graph_label="routing weights",
                                                         routing_file_name="routingWeights" + str(edge_considered))
                    edge_considered += 1

                for subedge in subedges_to_route:
                    key, mask, = subedge.key, subedge.mask
                    key_mask_combo = subedge.key_mask_combo
                    dest = subedge.postsubvertex
                    xd, yd, pd = dest.placement.processor.get_coordinates()
                    routing = lib_map.Routing(subedge)
                    xt, yt = SteinerTreeWeightedRouting.retrace_back_to_source(xd, yd, machine,
                                                                    nodes_info,
                                                                    dijkstra_tables,
                                                                    key, mask,
                                                                    key_mask_combo,
                                                                    routing,
                                                                    pd,
                                                                    BW_PER_ROUTE_ENTRY)
                    # SD Commented out 20/1/14 to remove extraneous printing.
                    # DijkstraRouting.printRoute(xt, yt, xs, ys, dijkstra_tables, routing)

                    subedge.routing = routing

                    routings.append(routing)

                    run_num += 1



                # SD Commented this out 20/1/14, to avoid extraneous printing
                # AS modified to debug format
                #print ""
                logger.debug("Route number {} completed from ({}, {}) "
                             "to ({}, {})".format(run_num, xs, ys, xd, yd))
                logger.debug("route took {}".format(SteinerTreeWeightedRouting.printRoute(xd, yd, xs, ys, dijkstra_tables, routing)))
                logger.debug("*********************************"
                             "**********************************")



                if (run_num % 5000) == 0:
                    logger.debug("{} routes done, please wait"
                                 "...".format(run_num))

        #finish_time = clock()

        #elapsed_time = finish_time - start_time

        #print("")
        #print("Routing finished! Created %d routes in %s seconds.") % (run_num, elapsed_time)
        #print("")
        logger.debug("gained benefit from {} pruned routings".format(pruned_sub_edges))
        return routings
