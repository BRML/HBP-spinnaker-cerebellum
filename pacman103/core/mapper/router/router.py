
import logging
logger = logging.getLogger( __name__ ) 

from pacman103.core.mapper import routing_algorithms
from pacman103.core.mapper.router import redundant_path_removal
from pacman103.core import exceptions, reports
from pacman103 import conf

import inspect

algorithms = conf.get_valid_components( routing_algorithms, "Routing" )

class Router(object):

    def __init__(self, dao):
        self.dao = dao


    def route(self):
        """
        Loads machine and subedge objects from the datastore, calls
        :py:func:`pacman103.core.mapper.route_raw` to generate placements, and
        stores them in the datastore.

        :param `pacman103.core.dao` dao:
            datastore containing machine and subvertex objects.
        """
        logger.info( "* Running Router *" )
        machine = self.dao.machine
        subedges = self.dao.subedges
        sub_nodes = self.dao.subvertices
        v = inspect.getmembers( routing_algorithms, inspect.isclass )
        try:
            router = algorithms[ conf.config.get( "Routing", "algorithm" ) ]
        except KeyError as e:
            raise ValueError( "Invalid router algorithm specified.  I don't" \
                              "know '%s'." % e )

        routings = router.route_raw(machine, sub_nodes, dao=self.dao)
        #routings = router.route_raw(machine, subedges)
        #generates router report for each chip
        reports.generate_routing_table_report(self.dao)
        #checks and optimisations
        #checks if there are inconsistant keys
        inconsistant_routings, redundant_paths = \
            self.check_for_inconsistant_routings(machine, self.dao.used_masks)
        if len(inconsistant_routings) > 0:
            Router.outputInconsistantRoutings(inconsistant_routings)

        #check if there are redundant paths which can be removed
        if len(redundant_paths) > 0:
            logger.debug( "Starting removal of redundant paths." )
            redundant_path_removal.redundant_path_removal(redundant_paths, machine)

        #recheck that theres no inconsistant routings after the
        # removal of redundant routes
        inconsistant_routings, redundant_paths = \
            Router.check_for_inconsistant_routings(machine, self.dao.used_masks)
        if len(redundant_paths) > 0:
            raise exceptions.RouteTableDSGException("redudant path removal didnt work")


        #check that theres no router with over 1000 entires
        self.check_for_table_supassing_maxiumum_level(machine)
        self.dao.routings = routings

        # Update occupancy information after path removal:
        for x in range(self.dao.machine.x_dim):
            for y in range(self.dao.machine.y_dim):
                if self.dao.machine.chip_exists_at(x, y):
                    chip = self.dao.machine.get_chip(x, y)
                    chip.router.occupancy = len(chip.router.cam)

        #update dao tracker variables for controller
        self.dao.done_router = True

    #takes a set of inconsistant routings and throws an exception
    @staticmethod
    def outputInconsistantRoutings(inconsistant_routings):
        #setup blurb
        output = "some routing key entries are inconsistant: "
        for entry in range(len(inconsistant_routings)):
            output = output + "[in chip ({}, {}) entry {} matches entry {} " \
                                "where they do not travel to the same destination  \n] " \
                                "".format(inconsistant_routings[entry][0],
                                          inconsistant_routings[entry][1],
                                          inconsistant_routings[entry][2],
                                          inconsistant_routings[entry][3])
        raise exceptions.RouteTableDSGException(output)


    #method to check that all routing entries on each router do not interfere with each other.
    #ASSUMES that the routing algorithum updated the cam of each router with its entries
    @staticmethod
    def check_for_inconsistant_routings(machine, used_masks):
        inconsistant_routing_key_entries = list()
        redundant_paths = list()
        #first you need to locate each routing table
        #  (located in the cam of each router)
        for x in range(machine.x_dim):
            for y in range(machine.y_dim):
                if machine.chip_exists_at(x, y):
                    router = machine.get_chip(x, y).router
                    inconsistant_routing_key_entries, redundant_paths = \
                        Router.check_routing_table(machine, x, y,
                                                   inconsistant_routing_key_entries,
                                                   redundant_paths, used_masks)
        return inconsistant_routing_key_entries, redundant_paths


    #method that cycles though all keys and masks to see if the same
    # key sets off more than one routing entry
    #does not assume the same mask for all entries
    @staticmethod
    def check_routing_table(machine, x, y, inconsistant_routing_key_entries,
                            redundant_paths, used_masks):
        #get key entry to check against
        router = machine.get_chip(x, y).router
        inconsistant_routing_key_entries, redundant_paths = \
            Router.check_entries(router, inconsistant_routing_key_entries,
                                 redundant_paths, x, y)
        return inconsistant_routing_key_entries, redundant_paths

    @staticmethod
    def check_entries(router, inconsistant_routing_key_entries, redundant_paths,
                      x, y):
        #get key entry to check against
        for to_check_key, entries in router.cam.items():
            if len(entries) > 1:
                initial_route = None
                initial_entry = None
                for routing_entry in entries:
                    if initial_route is None:
                        initial_entry = routing_entry
                        initial_route = routing_entry.route
                    else:
                        inconsistant_routing_key_entries, redundant_paths = \
                            Router.check_routes(initial_entry, routing_entry,
                                                inconsistant_routing_key_entries,
                                                redundant_paths, x, y)
        return inconsistant_routing_key_entries, redundant_paths

    #checks what type of inconsistant key it is
    @staticmethod
    def check_routes(initial_entry, other_entry,
                     inconsistant_routing_key_entries, redundant_paths, x, y):
        #same key, different destinations
        initial_key = initial_entry.original_key
        initial_entry_destination_chip_x, initial_entry_destination_chip_y = \
            initial_entry.routing.routing_entries[len(initial_entry.routing.routing_entries) -1].router.chip.get_coords()
        initial_entry_processor = initial_entry.routing.routing_entries[len(initial_entry.routing.routing_entries) -1].route
        other_entry_destination_chip_x, other_entry_destination_chip_y =\
            other_entry.routing.routing_entries[len(other_entry.routing.routing_entries) -1].router.chip.get_coords()
        other_entry_processor = other_entry.routing.routing_entries[len(other_entry.routing.routing_entries) -1].route

        #not same key, therefore inconsistant route
        if initial_key != other_entry.original_key:
            if not Router.duplicate(x, y, initial_entry, other_entry,
                                    inconsistant_routing_key_entries):
                logger.debug("adding inconsistant route where two different "
                             "keys make the same key combo")
                inconsistant_routing_key_entries.append([x, y, initial_entry,
                                                         other_entry])

        elif (initial_entry_destination_chip_x == other_entry_destination_chip_x) and \
             (initial_entry_destination_chip_y == other_entry_destination_chip_y) and \
             (initial_entry_processor == other_entry_processor):
            #same destination
            if not Router.duplicate(x, y, initial_entry,
                                    other_entry, redundant_paths):
                logger.debug( "two edges from the same soruce heading "
                              "to the same destination, therefore possible "
                              "redundant path")
                redundant_paths.append([x, y, initial_entry, other_entry])
        else:
        # different destinations
            if not Router.duplicate(x, y, initial_entry,
                                    other_entry, redundant_paths):
                logger.debug("initial x = {}, y = {}, entry = {}, "
                             "other = {}".format(x, y, initial_entry,
                                                 other_entry))
                redundant_paths.append([x, y, initial_entry, other_entry])
        return inconsistant_routing_key_entries, redundant_paths

    @staticmethod
    def duplicate(x, y, initial_entry, other_entry, entry_list):
        """
        checks that the new inconsiatncy hasnt already been recorded by the flipping of the entries
        """
        for entry in entry_list:
            if ((entry[2] == initial_entry and entry[3] == other_entry) or
               (entry[2] == other_entry and entry[3] == initial_entry)) and x == entry[0] and y == entry[1]:
                return True
        return False


    @staticmethod
    def check_for_table_supassing_maxiumum_level(machine):
        """
        # method that checks all routers looking for routers that have more than maxium capacity.
        #ASSUMES that the routing algorithum updated the occupancy of each router with its entries
        """
        logger.debug("checking that the routing table has less than the "
                     "maxiumum allowable entries")
        failed_routing_tables = []
        #locate any routing tables which are beyond the cap
        for x in range(machine.x_dim):
            for y in range(machine.y_dim):
                if machine.chip_exists_at(x, y):
                    #check how many entries are defaultable and subtract that from the count
                    routing_table = machine.get_chip(x, y).router.cam
                    defaultables = 0
                    for key in routing_table:
                        if (routing_table[key][0].defaultable):
                            defaultables = defaultables + 1
                    if machine.get_chip(x, y).router.occupancy-defaultables >=\
                            machine.get_chip(x, y).router.MAX_OCCUPANCY:
                        failed_routing_tables.append([x, y,
                                                      machine.get_chip(x, y).router.occupancy - defaultables])

                    logger.debug( "for chip ({}, {}) there are {} "
                                  "entries".format(x, y,
                                                   machine.get_chip(x, y).router.occupancy))

        #if located any broken routers, output chip positions and
        # routing table level
        if len(failed_routing_tables) != 0:
            logger.fatal("Broken routing tables: ", failed_routing_tables)
        if len(failed_routing_tables) != 0:
            #setup blurb
            output = "surpassed the maxiumum level of entries in the routing " \
                     "table for chip"
            if len(failed_routing_tables) > 1:
                output += "s located at"
            else:
                output += " located at"

            for entry in range(len(failed_routing_tables)):
                output = output + "[({}, {}) {}] ".format(failed_routing_tables[entry][0],
                                                          failed_routing_tables[entry][1],
                                                          failed_routing_tables[entry][2])

            raise exceptions.RouteTableDSGException(output)


