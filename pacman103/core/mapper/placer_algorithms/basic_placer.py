
import logging
logger = logging.getLogger(__name__)

from pacman103.lib import lib_map
from pacman103.core.mapper.placer_algorithms.abstract_placer import AbstractPlacer
from pacman103.core import exceptions

SDRAM_AVAILABLE = 119 * 1024 * 1024
CPU_AVAILABLE = 200000
DTCM_AVAILABLE = 2**15

class PlacementChip():
    
    def __init__(self, board_id, x, y, processors, sdram_size, cpu_speed, 
            dtcm_per_proc):
        self.board_id = board_id
        self.x = x
        self.y = y
        self.sdram_size = sdram_size
        self.cpu_speed = cpu_speed
        self.dtcm_per_proc = dtcm_per_proc
        
        self.core_available = list()
        next_id = 0
        self.free_cores = 0
        for proc in sorted(processors, key=lambda proc: proc.idx):
            if next_id != None:
                for _ in range(next_id, proc.idx):
                    self.core_available.append(False)
            self.core_available.append(True)
            self.free_cores += 1
            next_id = proc.idx + 1
        self.free_sdram = sdram_size
        
    def assign_core(self, sdram, core=None):
        chosen_core = None
        if core != None:
            self.core_available[core] = False
            chosen_core = core
        else:
            for i in range(0, len(self.core_available)):
                if self.core_available[i]:
                    self.core_available[i] = False
                    chosen_core = i
                    break
        
        self.free_cores -= 1
        self.free_sdram -= sdram
        
        return chosen_core
    
    def unassign_core(self, sdram, core):
        self.core_available[core] = True
        self.free_cores += 1
        self.free_sdram -= sdram

class BasicPlacer(AbstractPlacer):
    
    def __init__(self, dao):
        self.dao = dao
        self.chips = self.get_chips()
                
    def get_chips(self):
        chips = list()
        for x in range(self.dao.machine.x_dim):
            for y in range(self.dao.machine.y_dim):
                chip = self.dao.machine.get_chip(x, y)
                if not chip.is_virtual():
                    # TODO: The numbers should be from the machine!
                    self.chips.append(PlacementChip(chip.board_id, chip.x, chip.y,
                            chip.processors, SDRAM_AVAILABLE, CPU_AVAILABLE,
                            DTCM_AVAILABLE))
        return chips
              
    def place_all(self):
        """
        Loads machine and subvertex objects from the datastore, calls
        :py:func:`pacman103.core.mapper.place_raw` to generate placements, and
        stores them in the datastore.

        :param `pacman103.core.dao` dao:
            datastore containing machine and subvertex objects.
        """
        logger.info("* Running Placer *")
        
        # Load the machine and subvertices objects from the dao
        machine = self.dao.machine
        subvertices = self.dao.subvertices
        
        # Place the subvertices on processors
        placements = self.place_raw(machine, subvertices)
        
        # Store the results in the dao
        self.dao.placements = placements
        
        #update dao so thatc ontroller only calls the next stack aspect
        self.dao.done_placer = True

    def place_raw(self, machine, subvertices):
        """
        Generates placements by alloting processors to subvertices, taking those
        with placement contraints first.

        *Side effects*:
            irreversibly allocates processors in the machine via calls to
            :py:func:`pacman103.lib.lib_machine.Machine.palloc`, updates chips with
            references to their allocated processors and updates both allocated
            processors and subvertices with references to their placements.

        :param `pacman103.lib.lib_machine.Machine` machine:
            machine from which to allocate processors.
        :param list subvertices:
            list of :py:class:`pacman103.lib.graph.Subvertex` instances to
            allocate to processors.

        :returns:
            list of :py:class:`pacman103.lib.lib_map.Placement` instances.
        """
        placements = list()
        
        # Sort subvertices according to specificity of placement-requirements
        sort = lambda subvertex: subvertex.vertex.constraints.placement_cardinality
        subverts = sorted(subvertices, key=sort, reverse=True)

        # Iterate over subvertices and generate placements
        for subvertex in subverts:
            
            # Create and store a new placement
            placement = self.place_subvertex(subvertex, subvertex.get_resources,
                     subvertex.vertex.constraints)
            placements.append(placement)

        return placements
    
    def get_maximum_resources(self, constraints):
        """
        """
        maximum_sdram = 0
        maximum_cpu = 0
        maximum_dtcm = 0
        found_available_chip = False
        
        for chip in self.chips:
            
            x = None
            y = None
            p = None
            
            if constraints is not None:
                x = constraints.x
                y = constraints.y
                p = constraints.p
                
            if (((x is None) or (x == chip.x))
                    and ((y is None) or (y == chip.y))):
                
                if ((p is None) or (chip.core_available[p] == True)):
                    
                    chip_maxiumum_sdram_avilable = 0
                    if chip.free_cores > 1:
                        chip_maxiumum_sdram_avilable = chip.free_sdram / 2
                        found_available_chip = True
                    elif chip.free_cores == 1:
                        chip_maxiumum_sdram_avilable = chip.free_sdram
                        found_available_chip = True
                        
                    if chip_maxiumum_sdram_avilable > maximum_sdram:
                        maximum_sdram = chip_maxiumum_sdram_avilable
                        
                    if chip.cpu_speed > maximum_cpu:
                        maximum_cpu = chip.cpu_speed
                    
                    if chip.dtcm_per_proc > maximum_dtcm:
                        maximum_dtcm = chip.dtcm_per_proc
                        
        if not found_available_chip:
            if constraints is not None:
                raise Exception("No available resource could be found that fit"
                        + " the given constraints %s" % constraints)
            raise Exception("No further resources are available")       
        
        return lib_map.Resources(maximum_cpu, maximum_dtcm, maximum_sdram)

    def place_subvertex(self, resources, constraints):
        """
        method that places a subvert based on its memory requirements
        """
        placement_chip = None
        
        for chip in self.chips:
            x = None
            y = None
            p = None
            
            if constraints is not None:
                x = constraints.x
                y = constraints.y
                p = constraints.p
                
            if (((x is None) or (x == chip.x))
                    and ((y is None) or (y == chip.y))):
                
                if ((p is None) or (chip.core_available[p] == True)):
                    
                    if ((chip.free_cores > 0) 
                            and (chip.free_sdram >= resources.sdram)
                            and (chip.cpu_speed >= resources.clock_ticks)
                            and (chip.dtcm_per_proc >= resources.dtcm)):
                        placement_chip = chip
                        break
                    
        if placement_chip == None:
            raise Exception("Failed to place subvertex")
        
        core = placement_chip.assign_core(resources.sdram, p)
        return (placement_chip.x, placement_chip.y, core)
    
    def unplace_subvertex(self, x, y, p, resources):
        for chip in self.chips:
            if chip.x == x and chip.y == y:
                if chip.core_available[p]:
                    raise Exception("Attempt to unplace a processor that "
                            + "has not been assigned!")
                chip.unassign_core(resources.sdram, p)

    def place_virtual_subvertex(self, constraints, virtual_cores):
        pchip = None
        for chip in self.chips:
            if chip.x == constraints.x and chip.y == constraints.y:
                pchip = chip
                break
        if pchip is None:
            pchip = PlacementChip(-1, constraints.x, constraints.y, 
                    virtual_cores, 0, 0, 0)
            self.chips.append(pchip)
        core = pchip.assign_core(0, constraints.p)
        return (constraints.x, constraints.y, core) 
