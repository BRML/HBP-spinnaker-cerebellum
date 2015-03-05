__author__ = 'stokesa6'


import logging
logger = logging.getLogger( __name__ )

#takes a collection of routing key entries that are redundant and
# therefore one can be removed takes each redundant path and takes the key,
# locates it and removes entries till it reaches a branch or the source.
#LIMITATION: currently just takes the first entry as the one to be removed.
# No consideration of which has cheapest cost

def redundant_path_removal(redundant_paths, machine):
    counter = 0
    merges = 0
    for routing_table_entry in redundant_paths:
        counter += 1
        if routing_table_entry[3].previous_router_entry is None:
            merges += 1
        if len(routing_table_entry[2].router.cam.get(routing_table_entry[2].key)) > 1:
            logger.debug("Removing path that starts at chip {}, {}".format(
                    routing_table_entry[3].router.chip.x,
                    routing_table_entry[3].router.chip.y
            ))
            remove_route(routing_table_entry[2], routing_table_entry[3], machine)


# removes a route from dstination till it either hits the source or another branching entry
#ASSUMES same mask

def remove_route(dest_routing_table_entry, to_be_removed_path_entry, machine):
    #cycle though previous routing tables removing entries if possible
    found_branch = False

    entry = to_be_removed_path_entry.previous_router_entry
    previous_entry = None
    if entry is None:
        mergingOfOutboundRedundantPath(dest_routing_table_entry,
                                       to_be_removed_path_entry)


    while entry is not None and not found_branch:
        #if at root node, remove cloned entry and merge outputs
        if entry == to_be_removed_path_entry.previous_router_entry:
            mergingOfInboundRedundantPath(to_be_removed_path_entry,
                                          dest_routing_table_entry)
        elif len(entry.router.cam.get(entry.key)) > 1:
            logger.debug( "located outbound point at ({}, {})"
                          "".format(entry.router.chip.x,
                                    entry.router.chip.y))
            if number_of_outputs(entry.router.cam.get(entry.key)[0]) > 1:
                logger.debug( "located a entry with more than one output,"
                              " reducing output points" )
                remove_part_of_output(entry, previous_entry)
            else:
                logger.debug( "removing entry from router at ({},{})".format(
                    entry.router.chip.x,
                    entry.router.chip.y))
                entry.router.cam[entry.key].remove(entry)
            found_branch = True
        elif number_of_outputs(entry.router.cam.get(entry.key)[0]) > 1:
            logger.debug( "found a entry with more than 1 output, reducing output points" )
            remove_part_of_output(entry.router.cam.get(entry.key)[0], previous_entry)
            found_branch = True
        else:
            logger.debug( "removing entry from router at ({},{})".format(
                entry.router.chip.x,
                entry.router.chip.y))
            #update pointers
            previous_router_table = entry.router.cam
            del previous_router_table[entry.key]
            entry.router.occupancy = entry.router.occupancy -1
        previous_entry = entry
        entry = entry.previous_router_entry



def mergingOfOutboundRedundantPath(dest_routing_table_entry,
                                   to_be_removed_path_entry):
    logger.debug("Located outbound end of a redundant path, merging entries.")
    dest_output_route = dest_routing_table_entry.route
    other_output_route = to_be_removed_path_entry.route
    merged_output_route = dest_output_route | other_output_route
    dest_routing_table_entry.route = merged_output_route
    dest_routing_table_entry.defaultable = False
    for next_entry in to_be_removed_path_entry.next_router_entries:
        dest_routing_table_entry.next_router_entries.append(next_entry)
    for next_entry in dest_routing_table_entry.next_router_entries:
        next_entry.previous_router_entry = dest_routing_table_entry
    logger.debug("Merged route is {}.".format(bin(merged_output_route)))
    to_be_removed_path_entry.router.cam.get(dest_routing_table_entry.key).remove(to_be_removed_path_entry)
    to_be_removed_path_entry.router.occupancy -= 1


def mergingOfInboundRedundantPath(to_be_removed_path_entry,
                                  dest_routing_table_entry):
    list_of_entries = \
        to_be_removed_path_entry.router.cam.get(dest_routing_table_entry.key)
    logger.debug( "entry list = {}".format(list_of_entries) )
    #remove cloned entry
    list_of_entries.remove(to_be_removed_path_entry)
    to_be_removed_path_entry.router.occupancy = \
        to_be_removed_path_entry.router.occupancy -1
    logger.debug( "entry list = {}".format(list_of_entries) )
    #update hashtable
    del to_be_removed_path_entry.router.cam[dest_routing_table_entry.key]
    to_be_removed_path_entry.router.cam[dest_routing_table_entry.key] = list_of_entries
    logger.debug( "merge outputs from {},{}".format(
                    dest_routing_table_entry.router.chip.x,
                    dest_routing_table_entry.router.chip.y))
    #merge outputs
    dest_output_route = dest_routing_table_entry.route
    other_output_route = to_be_removed_path_entry.route
    merged_output_route = dest_output_route | other_output_route
    dest_routing_table_entry.route = merged_output_route
    dest_routing_table_entry.defaultable = False
    #update parents
    for next_entry in to_be_removed_path_entry.next_router_entries:
        dest_routing_table_entry.next_router_entries.append(next_entry)
    for next_entry in dest_routing_table_entry.next_router_entries:
        next_entry.previous_router_entry = dest_routing_table_entry



# takes a entry and removes the entry for it going down the wrong route
def remove_part_of_output(entry, previous_entry):

    logger.debug( "updateing direction" )
    direction = previous_entry.previous_router_entry_direction

    logger.debug( "entry id is {},{}".format(entry.router.chip.x,
                                             entry.router.chip.y))
    logger.debug( "previosu entry id {},{}"
                  "".format(previous_entry.router.chip.x,
                            previous_entry.router.chip.y) )
    logger.debug( "previoud direction route is {}".format(bin(direction)) )
    logger.debug( "the detected multipel route is {}".format(bin(entry.route)) )
    logger.debug( bin(previous_entry.route) )
    entry.route &= direction

    logger.debug( bin(entry.route) )

 # takes the route in a interger form and check the flags in binary form to determine how many output routes are
    # planned
def number_of_outputs(entry):
    logger.debug( "the binary form being checked is {}".format(bin(entry.route)))
    binary_form_of_route = bin(entry.route)
    counter = 0
    for binary_index in range(len(binary_form_of_route)):
        if binary_form_of_route[binary_index] == '1':
            counter += 1

    logger.debug( "located {} output routes".format(counter) )
    return counter