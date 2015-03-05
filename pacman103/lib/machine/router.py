__author__ = 'stokesa6'

import pacman103.lib.lib_map as lib_map

class Router:
    """
    Represents a SpiNNaker router. Contains a dictionary that represents the
    router Content Addressable Memory.

    *Side effects*:
        Upon instantiation, the parent chip is updated to include a reference
        to the instance.

    :param `pacman103.lib.lib_machine.Chip` chip: parent chip.
    """
    # Maximum number of routing table entries, CP: changed 7/8/13 as 24 reserved entries for system use
    MAX_OCCUPANCY = 1000


    def __init__(self, chip):
        # Record passed parameter
        self.chip = chip
        # Set up router memory
        self.cam = dict()
        self.occupancy = 0
        self.standard_mask = None
        self.linksuplist = []
        self.linksdownlist = []
        self.neighbourlist = []
        self.masks_used = dict()


    def get_working_links(self):
        """
        Returns a list of the links on this router which are active
        0=E, 1=NE, 2=N, 3=W, 4=SW, 5=S
        """
        return self.linksuplist


    def get_neighbours(self):
        """
        Returns a list of the neighbouring chips
        """
        return self.neighbourlist


    def ralloc(self, key, mask):
        """
        Allocates a :py:object:`pacman103.lib.lib_map.RoutingEntry` in the
        router CAM and returns it.

        The CAM dictionary is indexed by routing key, ignoring the bits not
        represented in the mask. Each value in the CAM dictionary is a list of
        the :py:object:`pacman103.lib.lib_map.RoutingEntry` objects that have
        been allocated at that key. When a novel key is presented to
        :py:func:`ralloc`, a new list is created for that key. If a novel key
        is presented when the CAM is full, the none-type object is returned.

        Varying masks are not currently handled. On the first call to
        :py:func:`ralloc`, a ``standard_mask`` is set. On all subsequent calls,
        an exception is thrown if the ``mask`` parameter is not equal to the
        ``standard_mask``.

        :param int key: routing key (<= 2^32-1).
        :param int mask: routing mask (<= 2^32-1).
        """
        #ABS commented out for virtual key space
        # Set the standard mask if this is the first call to ralloc
        #if self.standard_mask is None:
        #    self.standard_mask = mask
        # Raise an exception if the parameter mask is not equal to the standard
        #if mask != self.standard_mask:
         #   #TODO more descriptive error message and exception
        #    raise Exception('All routing-mask values must be equal.')
        # Mask off the routing key

        original_key = key
        key &= mask
        # ABS dont bother to check if theres room in the routing table, as the check is done
        # by the routing class (supports optimisations such as merging and default entry removal)
        # ABS do check that the key hasnt already used, if so then jsut append
        if key not in self.cam.keys():
            self.cam[key] = list()
        self.occupancy += 1

        #ABS keeps track of how many masks have been used in the entries of this router
        if not (mask in self.masks_used.keys()):
            self.masks_used[mask] = list()
            self.masks_used[mask].append(key)
        else:
            self.masks_used[mask].append(key)

        # Create a routing entry, store and return it
        routing_entry = lib_map.RoutingEntry(self, key, original_key, mask)
        self.cam[key].append(routing_entry)
        return routing_entry
