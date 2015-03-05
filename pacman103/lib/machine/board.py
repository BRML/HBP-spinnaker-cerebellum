__author__ = 'stokesa6'

class Board:
    """
    Represents a SpiNNaker board

    *Side effects*:
        Upon instantiation, the parent machine is updated to include a reference
        to this board instance.

    :param `pacman103.lib.lib_machine` machine: parent machine.
    :param int idx: board ID.
    :param int boardtype = the actual physical type of board (TODO: should be encoded in Serial ROM, but often isn't :-( )
    """

    def __init__(self, machine, idx, boardtype=0):
        # Store passed parameters
        self.machine = machine
        self.idx = idx
        self.boardtype = boardtype
        self.chips = list()


    def get_chips(self):
        """
        Returns a flattened list of the chips on the board.

        :returns: list of :py:object:`pacman103.lib.lib_machine.Chip` objects.
        """
        chips = list()
        for chip_row in self.chips:
            chips.extend(chip_row)
        return chips