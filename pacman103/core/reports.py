"""
    reports.py
    Creates a series of reports descriibing the output of the PACMAN103 mapping process.
    These reports cover:
        - Details of the target SpiNNaker machine
        - Partitioning of the user's network
        - Placement of sub-vertices onto cores
        - Routing information
"""

import time
import os
import struct
import numpy
import logging
from pacman103.lib import data_spec_constants
logger = logging.getLogger(__name__)

def generate_mapper_reports(dao):
    """
    Create a series of reports on the partition, placement, routing, etc.
    These are written to files in the report directory. The names of these 
    reports can be changed in the pacman.cfg .
    """
    generate_network_report(dao)
    generate_machine_report(dao)
    generate_placement_reports(dao)
    generate_routing_report(dao)
    generate_mem_usage_by_chip_report(dao)

def generate_data_generator_reports(dao):
    """
    Create reports on the physical files written to the machine, including
    the core_map, data specs and the decompilation of the appData files.
    These are written to files in the report directory. The names of these 
    reports can be changed in the pacman.cfg .
    """
    generate_memory_maps(dao)
    generate_coremap_report(dao)
    generate_appData_reports(dao)


def generate_network_report(dao):
    """
    Generate report on the user's network specification.
    """
    fileName = dao.get_reports_directory() + os.sep \
                      + "network_specification.rpt"
    try:
        fNetworkSpecification = open(fileName, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                                                                  % fileName)
    fNetworkSpecification.write("        Network Specification\n") 
    fNetworkSpecification.write("        =====================\n\n")
    timeDateString = time.strftime("%c")
    fNetworkSpecification.write("Generated: %s" % timeDateString)
    fNetworkSpecification.write(" for target machine '%s'" % dao.machine.hostname)
    fNetworkSpecification.write("\n\n")
    # Print information on vertices:
    fNetworkSpecification.write("*** Vertices:\n")
    for vertex in dao.vertices:
        label  = vertex.label
        model  = vertex.model_name
        size   = vertex.atoms
        flags  = vertex.flags
        flagsStr = bin(flags).replace("0b","")
        #params = vertex.parameters
        constraints = vertex.constraints
        #if len(params.keys()) == 0: 
        #    params = None
        if label is None:
            labelStr = "(NoName)"
        else:
            labelStr = "'%s'" % label
        fNetworkSpecification.write("Vertex %s, size: %d, flags: %s\n" 
                               % (labelStr, size, flagsStr))
        fNetworkSpecification.write("  Model: %s\n" % model)
        if constraints.x is not None: 
            if constraints.p is not None:
                constraintStr = "(x: %d, y: %d, p: %d)"  \
                % (constraints.x, constraints.y, constraints.p)
            else:
                constraintStr = "(x: %d, y: %d)"  \
                               % (constraints.x, constraints.y)
            fNetworkSpecification.write("  Placement constraint: %s\n"\
                                % constraintStr)
        #if params is None or len(params.keys()) == 0:
        #    fNetworkSpecification.write("  Parameters: None\n\n")
        #else:
        #    fNetworkSpecification.write("  Parameters: %s\n\n" % params)
        fNetworkSpecification.write("\n")
    
    # Print information on edges:
    fNetworkSpecification.write("*** Edges:\n")
    for edge in dao.edges:
        label        = edge.label
        model        = "No Model"
        if hasattr(edge, "connector"):
            model = edge.connector.__class__.__name__
        pre_v        = edge.prevertex
        post_v       = edge.postvertex
        #params       = edge.parameters
        constraints  = edge.constraints
        pre_v_sz     = pre_v.atoms
        post_v_sz    = post_v.atoms
        pre_v_label  = pre_v.label
        post_v_label = post_v.label
        if pre_v_label is None:
            pre_v_label = "(NoName)"
        if post_v_label is None:
            post_v_label = "(NoName)"
        if label is None:
            labelStr = "(NoName)"
        else:
            labelStr = "'%s'" % label
        edgeStr = "Edge %s from vertex: '%s' (%d atoms) to vertex: '%s' (%s atoms)\n" \
                   % (labelStr, pre_v_label, pre_v_sz, post_v_label, post_v_sz)
        fNetworkSpecification.write(edgeStr)
        fNetworkSpecification.write("  Model: %s\n" % model)
        #if params is None or len(params.keys()) == 0:
        #    fNetworkSpecification.write("  Parameters: None\n\n")
        #else:
        #    fNetworkSpecification.write("  Parameters: %s\n\n" % params)
        fNetworkSpecification.write("\n")

    # Close file:
    fNetworkSpecification.close()


def generate_machine_report(dao):
    """
    Generate report on the physical structure of the target SpiNNaker machine.
    """
    fileName = dao.get_reports_directory() + os.sep \
                      + "machine_structure.rpt"
    try:
        fMachineStruct = open(fileName, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                                                                  % fileName)
    fMachineStruct.write("        Target SpiNNaker Machine Structure\n")
    fMachineStruct.write("        ==================================\n\n")
    timeDateString = time.strftime("%c")
    fMachineStruct.write("Generated: %s" % timeDateString)
    fMachineStruct.write(" for target machine '%s'" % dao.machine.hostname)
    fMachineStruct.write("\n\n")
    
    x_dim = dao.machine.x_dim 
    y_dim = dao.machine.y_dim 
    fMachineStruct.write("Machine dimensions (in chips) x : %d  y : %d\n\n" \
                                                           % (x_dim, y_dim))

    fMachineStruct.write("Machine time step: %d micro-seconds\n" 
                                             % dao.machineTimeStep)
    fMachineStruct.write("Time scale factor: %d (simulation slow down factor)\n"
                                             % dao.time_scale_factor)

    # TODO: Add further details on the target machine.

    # Close file:
    fMachineStruct.close()


def generate_placement_reports(dao):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # File 1: Placement by vertex.
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    fileName = dao.get_reports_directory() + os.sep + "placement_by_vertex.rpt"
    try:
        fPlaceByVertex = open(fileName, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                                                                      % fileName)

    fPlaceByVertex.write("        Placement Information by Vertex\n")
    fPlaceByVertex.write("        ===============================\n\n")
    timeDateString = time.strftime("%c")
    fPlaceByVertex.write("Generated: %s" % timeDateString)
    fPlaceByVertex.write(" for target machine '%s'" % dao.machine.hostname)
    fPlaceByVertex.write("\n\n")

    # Store by core as we go
    # Get a list of chips used in this application:
    PROC_ID = 0    # Indices for entries in used_processors_by_chip
    PROC_OBJECT = 1
    used_processors_by_chip = dict()
    used_sdram_by_chip = dict()
    subvertex_by_processor = dict()
    
    for v in dao.vertices:
        vertexName = v.label
        vertexModel = v.model_name
        numAtoms    = v.atoms
        fPlaceByVertex.write("**** Vertex: '%s'\n" % vertexName)
        fPlaceByVertex.write("Model: %s\n" % vertexModel)
        fPlaceByVertex.write("Pop sz: %d\n" % numAtoms)
        fPlaceByVertex.write("Sub-vertices: \n")
        for sv in v.subvertices:
            lo_atom = sv.lo_atom
            hi_atom = sv.hi_atom
            numAtoms = hi_atom - lo_atom + 1
            placed_core = sv.placement.processor
            x, y, p = placed_core.get_coordinates()
            key = "%d,%d" % (x, y)
            used_procs = None
            if key in used_processors_by_chip.keys():
                used_procs = used_processors_by_chip[key]
            else:
                used_procs = list()
                used_sdram_by_chip.update({key: 0})
            subvertex_by_processor["%d,%d,%d" % (x, y, p)] = sv
            new_proc = [p, placed_core]
            used_procs.append(new_proc)
            used_processors_by_chip.update({key:used_procs})
            myString = "  Slice %d:%d (%d atoms) on core (%d, %d, %d) \n" \
                       % (lo_atom, hi_atom, numAtoms, x, y, p)
            fPlaceByVertex.write(myString)
        fPlaceByVertex.write("\n")
    # Close file:
    fPlaceByVertex.close()

    # File 2: Placement by core.
    # Cycle through all chips and by all cores within each chip.
    # For each core, display what is held on it.
    fileName = dao.get_reports_directory() + os.sep \
                      + "placement_by_core.rpt"
    try:
        fPlaceByCore = open(fileName, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                      % fileName)

    fPlaceByCore.write("        Placement Information by Core\n")
    fPlaceByCore.write("        =============================\n\n")
    timeDateString = time.strftime("%c")
    fPlaceByCore.write("Generated: %s" % timeDateString)
    fPlaceByCore.write(" for target machine '%s'" % dao.machine.hostname)
    fPlaceByCore.write("\n\n")

    # Now examine the machine in x, y order and print details of
    # only the used chips:
    for coord in dao.get_machine().get_coords_of_all_chips():
        xx, yy = coord['x'], coord['y']
        chip = dao.get_machine().get_chip(xx, yy)
        appCores = chip.appcores
        x = chip.x
        y = chip.y
        key = "%d,%d" % (x, y)
        if key in used_processors_by_chip.keys():
            fPlaceByCore.write("**** Chip: (%d, %d)\n" % (x, y))
            fPlaceByCore.write("Application cores: %d\n" % (appCores))
            for processor in used_processors_by_chip[key]:
                procID = processor[PROC_ID]
                procObj = processor[PROC_OBJECT]
                subvertex = subvertex_by_processor["%d,%d,%d" % (x, y, procID)]
                vertexLabel = subvertex.vertex.label
                vertexModel = subvertex.vertex.model_name
                vertexAtoms = subvertex.vertex.atoms
                lo_atom     = subvertex.lo_atom
                hi_atom     = subvertex.hi_atom
                numAtoms    = hi_atom - lo_atom + 1
                pStr = "  Processor %d: Vertex: '%s', pop sz: %d\n" \
                     % (procID, vertexLabel, vertexAtoms)
                fPlaceByCore.write(pStr)
                pStr = "               Slice on this core: %d:%d (%d atoms)\n" \
                     % (lo_atom, hi_atom, numAtoms)
                fPlaceByCore.write(pStr)
                pStr = "               Model: %s\n\n" % vertexModel
                fPlaceByCore.write(pStr)
            fPlaceByCore.write("\n")
    # Close file:
    fPlaceByCore.close()

    fileName = dao.get_reports_directory() + os.sep \
                      + "chip_sdram_usage_by_core.rpt"
    try:
        fMemUsedByCore = open(fileName, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                      % fileName)

    fMemUsedByCore.write("        Memory Usage by Core\n")
    fMemUsedByCore.write("        ====================\n\n")
    timeDateString = time.strftime("%c")
    fMemUsedByCore.write("Generated: %s" % timeDateString)
    fMemUsedByCore.write(" for target machine '%s'" % dao.machine.hostname)
    fMemUsedByCore.write("\n\n")

    for placement in dao.placements:
        subvert = placement.subvertex
        requirements = subvert.get_resources()
        processor = placement.processor
        x, y, p = processor.get_coordinates()
        if subvert.vertex.virtual:
            fMemUsedByCore.write(
                "SDRAM requirements for core ({},{},{}) is 0 KB\n".format(
                x, y, p))
        else:
            fMemUsedByCore.write(
                "SDRAM requirements for core ({},{},{}) is {} KB\n".format(
                x, y, p, int(requirements.sdram/1024.0)))
        key = "%d,%d" % (x, y)
        if not subvert.vertex.virtual:
            used_sdram_by_chip[key] += requirements.sdram


    for coord in dao.get_machine().get_coords_of_all_chips():
        xx, yy = coord['x'], coord['y']
        chip = dao.get_machine().get_chip(xx, yy)
        key = "%d,%d" % (chip.x, chip.y)
        try:
            used_sdram = used_sdram_by_chip[key]
            if used_sdram != 0:
                fMemUsedByCore.write(
                    "**** Chip: ({}, {}) has total memory usage of"
                    " {} KB out of a max of "
                    "{} MB \n\n".format(xx, yy,
                     int(used_sdram/1024.0),
                     int(data_spec_constants.SDRAM_AVILABLE/(1024.0*1024.0))))
        except KeyError:
            # Do Nothing
            pass
    
    # Close file:
    fMemUsedByCore.close()


def generate_routing_report(dao):
    """
    Generate report on the routing of sub-edges across the machine.
    """
    fileName = dao.get_reports_directory() + os.sep + "edge_routing_info.rpt"
    try:
        fRouting = open(fileName, "w")
    except IOError:
        logger.error("Generate_routing_reports: Can't open file %s for writing."\
                                                                      % fileName)
      
    fRouting.write("        Edge Routing Report\n")
    fRouting.write("        ===================\n\n")
    timeDateString = time.strftime("%c")
    fRouting.write("Generated: %s" % timeDateString)
    fRouting.write(" for target machine '%s'" % dao.machine.hostname)
    fRouting.write("\n\n")

    for e in dao.edges:
        from_v, to_v = e.prevertex, e.postvertex
        from_v_sz, to_v_sz = from_v.atoms, to_v.atoms
        fr_v_name, to_v_name = from_v.label, to_v.label
        string = "**** Edge '%s', from vertex: '%s' (size: %d)" % (e.label, 
                                                                 fr_v_name, 
                                                                 from_v_sz)
        string = "%s, to vertex: '%s' (size: %d)\n" % (string,   to_v_name, 
                                                                 to_v_sz)
        fRouting.write(string)
        fRouting.write("Sub-edges: %d\n" % len(e.subedges))
        for se in e.subedges:
            fr_sv, to_sv = se.presubvertex, se.postsubvertex
            fr_proc = fr_sv.placement.processor
            to_proc = to_sv.placement.processor
            if se.routing is not None:
                route_steps = se.routing.routing_entries
                route_len = len(route_steps)
                fr_core = "(%d, %d, %d)" % (fr_proc.get_coordinates())
                to_core = "(%d, %d, %d)" % (to_proc.get_coordinates())
                fr_atoms = "%d:%d" % (fr_sv.lo_atom, fr_sv.hi_atom)
                to_atoms = "%d:%d" % (to_sv.lo_atom, to_sv.hi_atom)
                string = "Sub-edge from core %s, atoms %s," % (fr_core, fr_atoms)
                string = "%s to core %s, atoms %s has route length: %d\n" % \
                          (string, to_core, to_atoms, route_len)
                fRouting.write(string)
                # Print route info:
                count_on_this_line = 0
                total_step_count = 0
                for step in route_steps:
                    if total_step_count == 0:
                       entry_str = "((%d, %d, %d)) -> " % (fr_proc.get_coordinates())
                       fRouting.write(entry_str)
                    chip_id = step.router.chip
                    entry_str = "(%d, %d) -> " % (chip_id.x, chip_id.y)
                    fRouting.write(entry_str)
                    if total_step_count == (route_len-1):
                       entry_str = "((%d, %d, %d))" % (to_proc.get_coordinates())
                       fRouting.write(entry_str)

                    total_step_count   += 1
                    count_on_this_line += 1
                    if count_on_this_line == 5:
                        fRouting.write("\n")
                        count_on_this_line = 0
                fRouting.write("\n")

        # End one entry:
        fRouting.write("\n")
    fRouting.flush()
    fRouting.close()

    return

def generate_memory_maps(dao):
    """
    Generate file showing the memory map of each chip.
    """
    # Get list of involved chips and the processors within each that
    # are actually part of the simulation:
    chipList = dict()
    for target in dao.executable_targets:
        x, y, p = target.targets[0]['x'], target.targets[0]['y'], target.targets[0]['p']
        chipID = (x, y)
        if chipID not in chipList.keys():
            chipList[chipID] = [p]
        else:
            chipList[chipID].append(p)
    # Create a list of load target addresses, indexed by processor ID:
    loadList = dict()
    for target in dao.load_targets:
        x, y, p = target.x, target.y, target.p
        procID = (x, y, p)
        if procID not in loadList.keys():
            loadList[procID] = [target.address]
        else:
            loadList[procID].append(target.address)

    # Cycle through these chips and write a memory map file for each:
    for chipID in chipList.keys():
        chip = dao.machine.get_chip(chipID[0], chipID[1])
        processors = chipList[chipID]
        write_memory_map_report(chip, processors, loadList, dao)


def write_memory_map_report(chip, processors, loadList, dao):
    """
    Write file for the given chip listing its memory regions and addresses.
    Params:
    - chip is the chip object for the particular chip under scrutiny
    - processors is a list of integers, the processors that are used on this
    chip.
    - dao is the database object.
    """
    fileName = "memMap_%d_%d.rpt" % (chip.x, chip.y)
    memMapDir = dao.get_reports_directory("chipMemMap")
    fullFileName = memMapDir + os.sep + fileName
    if (not os.path.exists(memMapDir)):
            os.makedirs(memMapDir)
    try:
        fMemMap = open(fullFileName, "w")
    except IOError:
        logger.error("Generate_memory_maps: Can't open file %s for writing."\
                                                               % fullFileName)
    title = "Memory Map for Chip (%d, %d)\n" % (chip.x, chip.y)
    underline = "=" * (len(title)-1)
    fMemMap.write("        " + title)
    fMemMap.write("        %s\n\n" % underline)
    timeDateString = time.strftime("%c")
    fMemMap.write("Generated: %s" % timeDateString)
    fMemMap.write(" for target machine '%s'" % dao.machine.hostname)
    fMemMap.write("\n\n")
    # Cycle through cores on ths chip that are used:
    processors.sort()
    for proc in processors:
        index = "%d %d %d" % (chip.x, chip.y, proc)
        procIdx = (chip.x, chip.y, proc)
        if procIdx not in loadList:
            raise Exception("INTERAL ERROR: write_mem_map_report " \
                            "- Load and Exec targets inconsistent!")
        # Get the base address for the appData file (i.e. where it 
        # will be loaded):
        loadAddr = loadList[procIdx][0]
        memRegions = dao.memMaps[index]
        fMemMap.write("Processor %d:     (Start address 0x%X)\n" % (proc, loadAddr))
        fMemMap.write(" Region    Rel.Addr  (Abs.Addr)          Size(bytes)\n")
        fMemMap.write("==========================================================\n")
        for region in memRegions:
            if region[data_spec_constants.REGION_SZ] > 0:
                # Address within SDRAM of this chip:
                absAddr  = memRegions[0][data_spec_constants.MEM_ARRAY][4+region[data_spec_constants.REGION_ID]]
                # Relative offset from start of appData file:
                relAddr  = memRegions[0][data_spec_constants.MEM_ARRAY][4+region[data_spec_constants.REGION_ID]]
                absAddr  = relAddr + loadAddr
                regionSz = region[data_spec_constants.REGION_SZ] * 4
                fMemMap.write("  %2d       " % region[data_spec_constants.REGION_ID])
                fMemMap.write("0x%6X (0x%8X)" % (relAddr, absAddr))
                fMemMap.write("   %8d (0x%6X)\n" % (regionSz, regionSz))
        fMemMap.write("\n")

    # Close file:
    fMemMap.close()


def generate_routing_table_report(dao, filename=None):
    #contents of the router in all chips as generated from the router.
    for coord in dao.get_machine().get_coords_of_all_chips():
        xx, yy = coord['x'], coord['y']
        chip = dao.get_machine().get_chip(xx, yy)
        if len(chip.router.cam) > 0:
            file_sub_name = None
            if filename is None:
                file_sub_name = "routing_table_%d_%d.rpt" % (xx, yy)
            else:
                file_sub_name = "routing_table_%d_%d_%s.rpt" % (xx, yy, filename)
            fileName = os.path.join(
                dao.get_reports_directory("routing_table_reports"),
                file_sub_name)
            try:
                output = open(fileName, "w")
            except IOError:
                logger.error("Generate_placement_reports: Can't open file"
                             " {} for writing.".format(fileName))

            output.write("router contains {} entries \n "
                         "\n".format(chip.router.occupancy))
            output.write("  Index   Key(hex)    Mask(hex)    Route(hex)    Src. Core -> [Cores][Links]\n")
            output.write("------------------------------------------------------------------------------\n")

            router_table = chip.router.cam
            entryCount = 0
            for key in router_table:
                index_and_size = entryCount
                index = index_and_size     & 0xFFFF
                size  = index_and_size>>16 & 0xFFFF
                totalEntries = size
                route = router_table[key][0].route
                key   = router_table[key][0].key
                mask  = router_table[key][0].mask
                hexRoute = uint32ToHexString(route)
                hexKey   = uint32ToHexString(key)
                hexMask  = uint32ToHexString(mask)
                routeTxt = expandRouteValue(route)
                coreID = "(%d, %d, %d)" % ((key>>24&0xFF),(key>>16&0xFF),(key>>11&0xF))
                entryStr = "    %d    %s      %s    %s       %s    %s\n" % \
                           (index, hexKey, hexMask, hexRoute, coreID, routeTxt)
                entryCount += 1
                output.write(entryStr)
            output.flush()
            output.close()


def generate_router_report(binaryRouterFileNameFullPath, chip, dao):
    """
    Generate a text file with the contents of the router in the chip
    given as a chip parameter. the filename of the .dat file must be supplied
    as the first argument.
    """
    components = binaryRouterFileNameFullPath.split(os.sep)
    routerTextFileName = components[-1].replace(".dat", ".txt")
    routerTextFileNameFullPath = dao.get_reports_directory("routers") + os.sep \
                      + routerTextFileName

    # open router.dat file for reading:
    try:
        fRouterSource = open(binaryRouterFileNameFullPath, "rb")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for reading."\
                     % binaryRouterFileNameFullPath)
    try:
        fRouterReport = open(routerTextFileNameFullPath, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file %s for writing."\
                     % routerTextFileNameFullPath)

    titleStr = "Routing Table for Chip (%d : %d)\n" % (chip.x, chip.y)
    underLine = "=" * (len(titleStr)-1)
    fRouterReport.write("        " + titleStr)
    fRouterReport.write("        " + underLine + "\n\n")
    timeDateString = time.strftime("%c")
    fRouterReport.write("Generated: %s" % timeDateString)
    fRouterReport.write(" for target machine '%s'" % dao.machine.hostname)
    fRouterReport.write("\n\n")
    
    fRouterReport.write("  Index   Key(hex)    Mask(hex)    Route(hex)    Src. Core -> [Cores][Links]\n")
    fRouterReport.write("------------------------------------------------------------------------------\n")

    # Unpack entries. Structure is:
    # Short 1: Index
    # Short 2: Key
    # Word  3: Mask
    # Word  4: Route
    # List terminates with Index = 0xFFFFFFFF
    totalEntries = 1024 # Default is all entries used.
    entryCount = 0
    while (entryCount < totalEntries):
        indexAndSize = struct.unpack('<I', fRouterSource.read(4))[0]
        if (indexAndSize == 0xFFFFFFFF):
            break
        index = indexAndSize     & 0xFFFF
        size  = indexAndSize>>16 & 0xFFFF
        totalEntries = size
        route = struct.unpack('<i', fRouterSource.read(4))[0]
        key   = long(struct.unpack('<i', fRouterSource.read(4))[0])
        mask  = struct.unpack('<i', fRouterSource.read(4))[0]
        hexRoute = uint32ToHexString(route)
        hexKey   = uint32ToHexString(key)
        hexMask  = uint32ToHexString(mask)
        routeTxt = expandRouteValue(route)
        coreID = "(%d, %d, %d)" % ((key>>24&0xFF),(key>>16&0xFF),(key>>11&0xFF)+1)
        entryStr = "    %d    %s      %s    %s       %s    %s\n" % \
                   (index, hexKey, hexMask, hexRoute, coreID, routeTxt)
        entryCount += 1
        fRouterReport.write(entryStr)
    
    # Close report file:
    fRouterReport.close()


def expandRouteValue(routeValue):
    """
    Convert a 32-bit route word into a string which lists the target cores and 
    links.
    """
    linksValue     = routeValue & 0x3F
    processorValue = (routeValue >> 6)
    # Convert processor targets to readable values:
    routeString = "["
    first = True
    for i in range(16):
        proc = processorValue & 0b1
        if proc != 0:
            if first:
                routeString += "%d" % i
                first = False
            else:
                routeString += ", %d" % i
        processorValue = processorValue >> 1
    routeString += "] ["
    # Convert link targets to readable values:
    linkLabels = {0:'E', 1:'NE', 2:'N', \
                  3:'W', 4: 'SW', 5:'S'}

    first = True
    for i in range(6):
        link = linksValue & 0b1
        if link != 0:
            if first:
                routeString += "%s" % linkLabels[i]
                first = False
            else:
                routeString += ", %s" % linkLabels[i]
        linksValue = linksValue >> 1
    routeString += "]"
     
    return routeString

def uint32ToHexString(number):
    """
    Convert a 32-bit unsigned number into a hex string.
    """
    bottom = number & 0xFFFF
    top    = (number >> 16) & 0xFFFF
    hexString = "%4.0X%4.0X" %(top, bottom)
    return hexString

def generate_coremap_report(dao):
    """
    Create a textual version of the core map in the reports directory.
    """
    # Set up an execution-control (barrier) matrix
    x_dim, y_dim = dao.machine.x_dim, dao.machine.y_dim
    barrier = numpy.zeros((x_dim, y_dim), dtype=numpy.int32)

    # Register each processor in the simulation with the barrier
    targets = dao.get_executable_targets()
    for target in targets:
        x, y, p = target.targets[0]['x'], target.targets[0]['y'], target.targets[0]['p']
        barrier[x][y] |= 1 << p

    fileName = dao.get_reports_directory() + os.sep + "core_map.rpt"
    try:
        fCoreMap = open(fileName, "w")
    except IOError:
        logger.error("Generate_coremap_report: Can't open file %s for writing."\
                      % fileName)

    fCoreMap.write("          Core Map Report\n")
    fCoreMap.write("          ===============\n\n")
    timeDateString = time.strftime("%c")
    fCoreMap.write("Generated: %s" % timeDateString)
    fCoreMap.write(" for target machine '%s'" % dao.machine.hostname)
    fCoreMap.write("\n\n")
    fCoreMap.write("Machine size: x: %d, y: %d\n\n" % \
                                       (dao.machine.x_dim, dao.machine.y_dim))

    fCoreMap.write("             x->\n")
    for y in range(y_dim):
        y_val = y_dim - y - 1
        if y == 1:
            fCoreMap.write("^ y: %3d  " % y_val)
        elif y == 2:
            fCoreMap.write("| y: %3d  " % y_val)
        elif y == 3:
            fCoreMap.write("y y: %3d  " % y_val)
        else:
            fCoreMap.write("  y: %3d  " % y_val)
        for x in range(x_dim):
            entry = bin(barrier[x][y_val]).replace("0b","")
            fCoreMap.write("[%s]" % entry)
        fCoreMap.write("\n")
    fCoreMap.write("\n")
        
    fCoreMap.close()


def generate_appData_reports(dao):
    """
    Decompile each appData file and save it in text format to the reports directory.
    """
    # Where will the final reports go?
    appDataReportsDir = dao.get_reports_directory("appData")
    # Where are the source appData binaries?
    appDataBinariesDir = dao.get_binaries_directory() 
    
    # Create a list of cores that will be processed:
    targetsList = dict()
    targets = dao.get_executable_targets()
    for target in targets:
        x, y, p = target.targets[0]['x'], target.targets[0]['y'], target.targets[0]['p']
        index = "%d: %d: %d" % (x, y, p)
        targetsList.update({index: True})
    

