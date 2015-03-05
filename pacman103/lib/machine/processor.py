__author__ = 'stokesa6'

class Processor:
    """
    Represents a SpiNNaker processor.

    *Side effects*:
        Upon instantiation, the parent chip is updated to include a reference
        to the instance.

    :param `pacman103.lib.lib_machine.Chip` chip: parent chip.
    :param int idx: processor ID.
    :param int phyid= the actual physical core ID this virtual application core corresponds to on the chip
    """

    def __init__(self, chip, idx, phyid=None):
        # Store passed parameters
        self.chip = chip
        self.idx = idx
        self.phyid = phyid
        
        #set up reference to the app region pointer table
        self.region_table_start_addr = None

    def get_coordinates(self):
        """
        Returns the processor coordinates.

        :returns: tuple of (chip_x, chip_y, processor_idx) coordinates.
        """
        return self.chip.x, self.chip.y, self.idx

    def to_string(self):
        return "{}:{}:{}".format(self.chip.x, self.chip.y, self.idx)