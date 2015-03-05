__author__ = 'stokesa6'
from pacman103.lib.machine import processor
from pacman103.lib.machine import router
from pacman103.lib.data_spec_constants import SDRAM_AVILABLE
from pacman103.lib.lib_map import Resources
from pacman103.core import exceptions

class Chip:
    """
    Represents a SpiNNaker chip. Instantiates a list of
    :py:object:`pacman103.lib.lib_machine.Processor` objects and a
    :py:object:`pacman103.lib.lib_machine.Router` object with which to populate
    the chip.

    :param `pacman103.lib.lib_machine.Machine` machine: parent machine.
    :param int x: x-coordinate of the chip.
    :param int y: y-coordinate of the chip.
    :param int n_proc: number of working application processors in the chip.
    """

    def __init__(self, machine, x, y, boardid, n_proc=16, virtual=False):
        
        # Record object attributes
        self.machine = machine
        self.boardid = boardid
        self.appcores = n_proc
        self.virtual = virtual
        self.x = x
        self.y = y
        self._processors = dict()
        
        # Generate the chip's processors (processors are added later if DYNAMIC)
        if machine.machine_type != "dynamic" or self.virtual:
            for x in xrange(n_proc):
                if self.virtual:
                    self._processors[x] = processor.Processor(self, x)
                else:
                    self._processors[x+1] = processor.Processor(self, x+1)

        # Generate the chip's router
        self.router = router.Router(self)
        
        # Track SDRAM usage during Data Generation process:
        self.sdramUsed = 0
        
        # Used by Host-side SpecExecutor to track memory allocation:
        self.memoryMap = list() # of start-end address pairs for reserved memory

    '''
    return the string based version of this chip
    '''
    def toString(self):
        return "{}:{}".format(self.x, self.y)

    def get_coords(self):
        return self.x, self.y

    def get_processor(self, idx):
        if idx in self._processors:
            return self._processors[idx]
        else:
            raise exceptions.PacmanException("no processor with id "
                                             "{}".format(idx))

    def get_processors(self):
        return self._processors.values()

    def remove_processor(self, processor_id):
        del self._processors[processor_id]

    def add_processor(self, chip_processor, phyid):
        if phyid in self._processors.keys():
            raise exceptions.PacmanException("trying to add a "
                                             "processor that already exists")
        else:
            self._processors[phyid] = chip_processor

    def is_virtual(self):
        return self.virtual

