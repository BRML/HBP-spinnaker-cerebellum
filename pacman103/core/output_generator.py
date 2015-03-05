from array import array
import ConfigParser
import logging
import numpy
import os
import os.path
import pickle
import shutil

from pacman103 import conf
from pacman103.lib import lib_map, data_spec_constants
from pacman103.core import data_spec_executor, exceptions, reports
from pacman103.core.dao import DAO
from pacman103.core.process_bar import ProgressBar

logger = logging.getLogger(__name__)


"""
Static functions for generating executable specifications and simulation
data structures.

"""

def generate_output(dao):
    """
    Loads the machine objects from the datastore, calls
    :py:func:`pacman103.core.output_generator.generate_output_raw` to generate
    load targets and executable targets, and stores the result in the datastore.

    :param `pacman103.core.dao` dao:
        datastore containing a machine object.

    """
    machine = dao.get_machine()
    #checks if the folders for the binery and reports exists already.
    check_directories_exist(dao)
    generate_output_raw(dao)
    if conf.config.getboolean("Reports", "reportsEnabled"):
        reports.generate_data_generator_reports(dao)
    
    # Pickle outputs for reload
    directory = DAO.get_binaries_directory()
    load_targets_path = os.path.join(directory, "pickled_load_targets")
    executable_targets_path = os.path.join(directory, "pickled_executable_targets")
    mem_write_targets_path = os.path.join(directory, "pickled_mem_write_targets")
    
    try:
        load_targets_file = open(load_targets_path, "wb")
        pickle.dump(dao.load_targets, load_targets_file, protocol=pickle.HIGHEST_PROTOCOL)
        load_targets_file.close()
        executable_targets_file = open(executable_targets_path, "wb")
        pickle.dump(dao.executable_targets, executable_targets_file, protocol=pickle.HIGHEST_PROTOCOL)
        executable_targets_file.close()
        mem_write_targets_file = open(mem_write_targets_path, "wb")
        pickle.dump(dao.mem_write_targets, mem_write_targets_file, protocol=pickle.HIGHEST_PROTOCOL)
        mem_write_targets_file.close()
    except Exception as e:
        print e.message
    
        
def reload_output(dao, reload_time):
    logger.info("Reloading targets from %s" % reload_time)
    directory = DAO.get_binaries_directory(reload_time=reload_time)
    load_targets_path = os.path.join(directory, "pickled_load_targets")
    executable_targets_path = os.path.join(directory, "pickled_executable_targets")
    mem_write_targets_path = os.path.join(directory, "pickled_mem_write_targets")
    try:
        load_targets_file = open(load_targets_path, "rb")
        dao.load_targets = pickle.load(load_targets_file)
        load_targets_file.close()
        executable_targets_file = open(executable_targets_path, "rb")
        dao.executable_targets = pickle.load(executable_targets_file)
        executable_targets_file.close()
        mem_write_targets_file = open(mem_write_targets_path, "rb")
        dao.mem_write_targets = pickle.load(mem_write_targets_file)
        mem_write_targets_file.close()
    except Exception as e:
        print e.message

def check_directories_exist(dao):
    binary_dir = dao.get_binaries_directory()
    if (not os.path.exists(binary_dir)):
        os.makedirs(binary_dir)

def generate_output_raw(dao):
    """
    The nitty gritty.
    Generates load targets and executable targets comprising the simulation, and
    for when individual memory locations are to be written, generates memWrites.

    This is now largely finished. Data structures are generated for edges
    and the data structure generation for vertices is merely a prototype.

    *Side effects*:
        writes data structures for the load targets to files in the binaries directories

    :returns:
        Nothing       
    """

    executable_targets, load_targets, mem_write_targets = list(), list(), list()
    chipsUsed = set()
    progress_bar = ProgressBar(len(dao.placements))

    # If we have host-side Spec Execution, execute all Data Specs now:
    try:
        dao.useHostBasedSpecExecutor = \
            conf.config.getboolean( "SpecExecution", "specExecOnHost" )
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        raise Exception( "SpecExecutor could not find config information"
                         " indicating where Spec Execution should occur." )
    
    chips = None
    if dao.useHostBasedSpecExecutor == True:
        chips = dict()
        for placement in dao.placements:
            (x, y, p) = placement.processor.get_coordinates()
            key = "{}:{}".format(x, y)
            if not key in chips:
                chips[key] = data_spec_executor.Chip(x, y)

    for placement in dao.placements:
        if not placement.subvertex.vertex.is_virtual():
            
            start_addr = None
            if dao.useHostBasedSpecExecutor == True:
                dao.spec_executor = data_spec_executor.SpecExecutor()
                
                (x, y, p) = placement.processor.get_coordinates()
                key = "{}:{}".format(x, y)
                chip = chips[key]

                start_addr = chip.sdram_used + \
                    data_spec_constants.SDRAM_BASE_ADDR
                dao.spec_executor.setup(chip)
            
            subvertex = placement.subvertex

            myExecTargets, myLoadTargets, myMemWriteTargets = \
                 subvertex.generateDataSpec(placement.processor, dao)

            # Add this core to the list of targets
            if myExecTargets is not None:
                executable_targets.append(myExecTargets)
            
            # Append the new dataSpec file to the list of load targets:
            if myLoadTargets is not None and len(myLoadTargets) > 0:
                load_targets.extend(myLoadTargets)
            
            # Add required memory writes to the list of writes:
            if myMemWriteTargets is not None and len(myMemWriteTargets) > 0:
                mem_write_targets.extend(myMemWriteTargets)
            
            x, y, p = placement.processor.get_coordinates()
            chipsUsed.add((x, y))
            
            hostname = dao.machine.hostname
            
            if dao.useHostBasedSpecExecutor == True:
                (x, y, p) = placement.processor.get_coordinates()
                f_out = os.path.join(
                    dao.get_binaries_directory(),
                    "%s_appData_%d_%d_%d.dat" % (hostname, x, y, p)
                )
                dao.spec_executor.finish(f_out)

                # TODO: Bring the following in line / neaten
                # ----------------------------------------------
                # Keep information on the memory region locations
                # for later report generation:
                index = "%d %d %d" % (x, y, p)
                dao.memMaps[index] = [
                    [i, s.wr_ptr_aligned, s.wr_ptr_offset, s.size, \
                                               s.memory, s.unfilled] \
                    if s is not None else [i, 0, 0, 0, [], False]
                        for (i, s) in enumerate(dao.spec_executor.memory_slots)
                ]

                # Add the files produced by the Spec Executor to the
                # list of files to load:
                load_targets.append(lib_map.LoadTarget(
                    f_out, x, y, p, start_addr))
                mem_write_targets.append(lib_map.MemWriteTarget(
                    x, y, p, 0xe5007000 + 128*p + 112, start_addr))
        progress_bar.update()

    # populate the DAO with executable, load and memory writing requirements
    dao.set_executable_targets(executable_targets)
    dao.set_load_targets(load_targets)
    dao.set_mem_write_targets(mem_write_targets)

    # Generate core map and routing table binaries for each chip
    for coord in dao.machine.get_coords_of_all_chips():
        x, y = coord['x'], coord['y']
        chip = dao.machine.get_chip(x, y)
        routeCount = get_route_count(chip)
        if (routeCount > 0 or (x, y) in chipsUsed) and not chip.is_virtual():
            fileName  = generate_routing_table(chip, routeCount, dao)
            if (conf.config.getboolean("Reports", "reportsEnabled") and
                conf.config.getboolean("Reports", "writeRouterReports") and
                conf.config.getboolean("Reports", "writeRouterDatReport")):
                reports.generate_router_report(fileName, chip, dao)
    
            # Place in the list of targets to load at 119.5MB depth in the SDRAM
            if not chip.virtual:
                load_targets.insert(
                    0, lib_map.LoadTarget(
                        fileName, chip.x, chip.y, 0,
                        data_spec_constants.ROUTING_TABLE_ADDRESS
                    )
                )
    progress_bar.end()
            
def get_route_count(chip):
    defaulted = 0
    for key in chip.router.cam:
        if chip.router.cam[key][0].defaultable:
            defaulted += 1
    return len(chip.router.cam) - defaulted

def generate_routing_table(chip, size, dao):
    """
    This takes a chip object, and from it generates the routing table entry file for
    its router in binary format of form (per CP/ST 6th Aug 2013):

    typedef struct rtr_entry
    {
        ushort vrid;                  //!< Index of this routing entry (virtual)
        ushort blocksize;             //!< How many contigious entries in this section
        uint route;                   //!< Route word
        uint key;                     //!< Key word
        uint mask;                    //!< Mask word
    } rtr_entry_t;
        
    A final entry with all fields set to all-1s will act as a final delimiter

    This is an implementation which positions the first route at position 0, and all
    further entries contiguously follow.
    
    There is no attempt at optimisation, as all masks are fixed at 11 bits and are
    not expected to overflow the 1k entries in the routing table.
    ABS shouldnt need to optimise, as the router should be resposbile for optimisations
    :returns:
        a file in the binaries directory (spinnaker_package_103/binaries/) or None if not required
        a counter of the number of routes that were inserted into the routing table
    """    

    output_file=None
    
    # open file
    fname = dao.get_binaries_directory() + os.sep \
            + "%s_router_%d_%d.dat" % (chip.machine.hostname, chip.x, chip.y)
    try:
        output_file = open(fname, "wb")
    except IOError:
        raise exceptions.RouteTableDSGException('Got a File Error with %s',
                fname)

    vrid = 0
    
    for maskedkey in chip.router.cam:
        # as entries are contiguous can just consolidate and blat them out 
        compiled = vrid | (size<<16)
        destination_route=0
        defaultable=True
        destination_route = chip.router.cam[maskedkey][0].route
        mask = chip.router.cam[maskedkey][0].mask

        if not chip.router.cam[maskedkey][0].defaultable:
            defaultable = False


        output_me = array('I', [compiled, destination_route, maskedkey, mask])
        # 'I' means unsigned Integers
        if defaultable==False:
            output_me.tofile(output_file)
            vrid +=1

    # send delimiter (all 1s) before closing the file off
    compiled=mykey=mymask=myroute=0xFFFFFFFF
    output_me = array('I', [compiled, mykey, mymask, myroute])
    output_me.tofile(output_file)
    output_file.close()
    return fname
