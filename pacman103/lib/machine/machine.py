import logging
import numpy
from pacman103.core.spinnman.scp.scp_message import SCPMessage
from pacman103.core.spinnman.scp import scamp
from pacman103.core import exceptions
from pacman103.core.spinnman.scp.scp_error import SCPError
from pacman103.lib.machine import processor, chip as board_chip, board
from pacman103.core.spinnman.interfaces.transceiver import Transceiver
from pacman103 import conf


logger = logging.getLogger(__name__)


class Machine(object):
    """
    Represents a SpiNNaker machine. Instantiates an exploration of the machine
    populating it with a list of :py:object:`pacman103.lib.lib_machine.Chip`
    objects, and also link information, taking into account faults and
    machine dimensions

    :param string host: IP hostname of the machine.
    :param string type: can be "spinn2"/"spinn3"/"spinn4"/"spinn5" which statically map to the board types,
     "unwrapped" for a static machine of the requested dimensions (default x=8, y=8) that does not wrap around,
     "wrapped" for a static machine that DOES wrap around, or
     "dynamic" for something which auto-discovers the status of a network attached machine.
    :param int x: expected x-dimensions of the machine when statically defining.
    :param int y: expected y-dimension of the machine when statically defining.
        these will be set as an 8x8 (Spinn4/5) static configuration if not explicitly specified
    """

    def __init__(self, hostname, x=None, y=None, type="dynamic",
                 virtual_verts=list()):

        # Store passed parameters
        self.hostname = hostname
        self.machine_type = type
        self.link_count = 0
        self.virtual_chips = virtual_verts

        # Generate the grid of chips and processors
        self.boards = list()
        self._chips = dict()
        self.x_dim = None
        self.y_dim = None
        self.initialise_board(x, y, self.machine_type)

    def initialise_board(self, x, y, machine_type):
        if machine_type != "dynamic":

            boardid = board.Board(self, 0, machine_type)
            self.boards.append(boardid)
            self.create_board_chips(x, y, boardid, machine_type)
            self.remove_downed_cores()
            self.remove_downed_chips()
            self.initlize_neighbour_links(machine_type)
            self.add_virtual_chips()
        else:
            conn = Transceiver(self.hostname, 17893)
            self.determine_board_structure(self.hostname, x,
                                           y, machine_type, conn)
            self.remove_downed_cores()
            self.remove_downed_chips()
            self.determine_board_routing(self.hostname, conn)
            self.add_virtual_chips()

    def initlize_neighbour_links(self, machine_type):
        # the connectivity information for board types SPINN2/3/4/5
        if machine_type == "spinn2" or machine_type == "spinn3":
            self.initlize_neighbour_links_for_4_chip_board()
        elif (machine_type == "spinn4" or machine_type == "spinn5" or
             machine_type == "unwrapped" or machine_type == "wrapped"):
            self.initlize_neighbour_links_for_other_boards(machine_type)
        else:
            raise Exception(
                "EXPLORE: I don't know how to interconnect the chips of "
                "this machine, needs to be explored dynamically")
        logger.debug(
            "Static Allocation Complete. %d" \
            "calculated app cores and %d" \
            "links!" % (
                len(self.get_processors()),
                self.link_count / 2
            )
        )
        # links are divided by 2 as there are 2 ends to each link!


    def initlize_neighbour_links_for_4_chip_board(self):
        chipx = 0
        chipy = 0
        self.get_chip(chipx, chipy).router.linksuplist = [0, 1, 2, 5]
        self.get_chip(chipx, chipy).router.linksdownlist = [3, 4]
        self.get_chip(chipx, chipy). \
            router.neighbourlist = [{'x': 1, 'y': 0, '16bit': 256,
                                     'object': self.get_chip(1, 0).router},
                                    {'x': 1, 'y': 1, '16bit': 257,
                                     'object': self.get_chip(1, 1).router},
                                    {'x': 0, 'y': 1, '16bit': 1,
                                     'object': self.get_chip(0, 1).router},
                                    None, None,
                                    {'x': 0, 'y': 1, '16bit': 1,
                                     'object': self.get_chip(0, 1).router}]
        chipx = 0
        chipy = 1
        self.get_chip(chipx, chipy).router.linksuplist = [0, 1, 2, 5]
        self.get_chip(chipx, chipy).router.linksdownlist = [3, 4]
        self.get_chip(chipx, chipy). \
            router.neighbourlist = [{'x': 1, 'y': 1, '16bit': 257,
                                     'object': self.get_chip(1, 1).router},
                                    {'x': 1, 'y': 0, '16bit': 256,
                                     'object': self.get_chip(1, 0).router},
                                    {'x': 0, 'y': 0, '16bit': 0,
                                     'object': self.get_chip(0, 0).router},
                                    None, None,
                                    {'x': 0, 'y': 0, '16bit': 0,
                                     'object': self.get_chip(0, 0).router}]
        chipx = 1
        chipy = 0
        self.get_chip(chipx, chipy).router.linksuplist = [2, 3, 4, 5]
        self.get_chip(chipx, chipy).router.linksdownlist = [0, 1]
        self.get_chip(chipx, chipy). \
            router.neighbourlist = [None, None,
                                    {'x': 1, 'y': 1, '16bit': 257,
                                     'object': self.get_chip(1, 1).router},
                                    {'x': 0, 'y': 0, '16bit': 0,
                                     'object': self.get_chip(0, 0).router},
                                    {'x': 0, 'y': 1, '16bit': 1,
                                     'object': self.get_chip(0, 1).router},
                                    {'x': 1, 'y': 1, '16bit': 257,
                                     'object': self.get_chip(1, 1).router}]
        chipx = 1
        chipy = 1
        self.get_chip(chipx, chipy).router.linksuplist = [2, 3, 4, 5]
        self.get_chip(chipx, chipy).router.linksdownlist = [0, 1]
        self.get_chip(chipx, chipy). \
            router.neighbourlist = [None, None,
                                    {'x': 1, 'y': 0, '16bit': 256,
                                     'object': self.get_chip(1, 0).router},
                                    {'x': 0, 'y': 1, '16bit': 1,
                                     'object': self.get_chip(0, 1).router},
                                    {'x': 0, 'y': 0, '16bit': 0,
                                     'object': self.get_chip(0, 0).router},
                                    {'x': 1, 'y': 0, '16bit': 256,
                                     'object': self.get_chip(1, 0).router}]
        self.link_count = 16
        #add the neighbour list with x and y coordinated, the 16bit
        # version and the target router object

    def initlize_neighbour_links_for_other_boards(self, machine_type):
        # these boards are not x*y, so need to be a bit more
        # savvy about the connectivity
        for i in xrange(self.x_dim):
            for j in xrange(self.y_dim):
                if self.chip_exists_at(i, j):
                    # can only run where we have a physical chip!
                    for k in xrange(6):
                        targetx = i
                        targety = j
                        if k == 0 or k == 1:
                            targetx += 1
                        if k == 1 or k == 2:
                            targety += 1
                        if k == 3 or k == 4:
                            targetx -= 1
                        if k == 4 or k == 5:
                            targety -= 1
                        if machine_type == "wrapped":
                            # print "x:",i,"y:",j,"  Dims:",self.x_dim,\
                            #   self.y_dim,"-- Orig: ",targetx,targety,
                            targetx = targetx % self.x_dim
                            targety = targety % self.y_dim
                        if (targetx < self.x_dim and
                            targetx >= 0 and
                            targety < self.y_dim and
                            targety >= 0):
                            # ensure that the connected chip would be
                            # inside the x/y dimension parameters
                            if self.chip_exists_at(targetx, targety):
                                self.get_chip(i, j).router.linksuplist.append(k)
                                self.get_chip(i, j).router.neighbourlist.append(
                                    {'x': targetx,
                                     'y': targety,
                                     '16bit': (targetx * 256) + targety,
                                     'object': self.get_chip(targetx, targety).router})
                                self.link_count += 1
                                # ensure that the target chip actually exists
                            else:
                                self.get_chip(i, j).router.linksdownlist.append(k)
                                self.get_chip(i, j).router.neighbourlist.append(None)
                        else:
                            self.get_chip(i, j).router.linksdownlist.append(k)
                            self.get_chip(i, j).router.neighbourlist.append(None)

    def create_board_chips(self, x, y, boardid, machine_type):
        # if x and y are none, assume a 48 chip board
        if x is None and y is None:
            x = 8
            y = 8
        self.x_dim, self.y_dim = x, y
        logger.debug("xdim = {} and ydim  = {}".format(self.x_dim, self.y_dim))
        board48gaps = [(0, 4), (0, 5), (0, 6), (0, 7), (1, 5), (1, 6), (1, 7),
                       (2, 6), (2, 7), (3, 7), (5, 0), (6, 0), (6, 1), (7, 0),
                       (7, 1), (7, 2)]
        for i in xrange(self.x_dim):
            for j in xrange(self.y_dim):
                coords = (i, j)
                if (machine_type == "spinn4" or machine_type == "spinn5") \
                        and coords in board48gaps:
                    pass
                    # a chip doesn't exist in this static position
                    # on these boards, so nullify it
                else:
                    chip = board_chip.Chip(self, i, j, 0)
                    self._chips[chip.toString()] = chip
                    boardid.chips.append(chip)

    def determine_board_structure(self, hostname, x, y, machine_type, conn):

        # on network
        xdims, ydims = conn.check_target_machine(hostname, x, y)
        self.x_dim = xdims
        self.y_dim = ydims

        # ok, we have an active, booted and numbered board,
        # let's explore the chips (mmmmmmm, chips)

        # TODO - in future we will have board IDs (see ST), so will require modifying for chip positions on boards
        #         in the meantime everything will be on notional
        # board 0, which is constructed of a board type !
        boardid = board.Board(self, 0, machine_type)
        self.boards.append(boardid)

        for xx in range(xdims):
            # as a list has a single dimension this for each x, creates a
            # list of ys to sit as a second dimension
            for yy in range(ydims):
                conn.select(xx, yy, 0)
                # check here for non-responsive/non-existent chips
                try:
                    ycoord = int(numpy.fromstring(
                        conn.memory_calls.read_mem(0xf5007f00,
                                                   scamp.TYPE_BYTE, 1),
                        dtype=numpy.uint8))
                    xcoord = int(numpy.fromstring(
                        conn.memory_calls.read_mem(0xf5007f01,
                                                   scamp.TYPE_BYTE, 1),
                        dtype=numpy.uint8))
                    if xcoord != xx or ycoord != yy:
                        raise Exception("EXPLORE: Incorrect chip coordinates, "
                                        "whacky wiring or provided dimensions?")

                    # first let's create the chip objects within the machine
                    # (no live cores yet) and add to the machine and board
                    chipid = board_chip.Chip(self, xx, yy, boardid, 0)
                    self._chips[chipid.toString()] = chipid
                    boardid.chips.append(chipid)

                    # then check the virtual core to physical core registers
                    # for mappings and up/down any wear-out/failures after mfg
                    #  mapped out by ST in SC&MP/SARK, but reflected here.
                    #thresholding to limit max id
                    if conf.config.has_option("Machine", "core_limit"):
                        core_limit = conf.config.getint("Machine", "core_limit")
                    else:
                        core_limit = 16

                    for i in range(1, core_limit + 1):
                        phycpu = int(numpy.fromstring(
                            conn.memory_calls.read_mem(0xf5007fa8 + i,
                                                       scamp.TYPE_BYTE, 1),
                            dtype=numpy.int8))
                        if phycpu != -1:
                            newProc = processor.Processor(chipid, i, phycpu)
                            chipid.add_processor(newProc, i)
                            chipid.appcores += 1
                            #print "i: ",i, "with cumulative ",chipid.appcores
                            # add the checked list of application
                            # processors to the machine's pool of cores

                except SCPError:
                    #print "(%d,%d): Chip down / Not in Grid" % (int(xx),int(yy))
                    pass
                    # catch this as don't want an exception here as
                    #  topology might not be exactly x*y with functional chips


    '''
       adds any virtual chips to the machien structure and connects them to the
       real machine chips via a defined link

    '''
    def add_virtual_chips(self):
        for virtual_chip in self.virtual_chips:
            #create and add a new chip
            coords = virtual_chip.virtual_chip_coords
            #check that the virtual chip does not corrapsond to a real chip
            if self.chip_exists_at(coords['x'], coords['y']):
                raise exceptions.PacmanException("the virtual chip currently "
                                                 "corrasponds to a real chip, "
                                                 "therefore fails")

            chip = board_chip.Chip(self, coords['x'], coords['y'], -1, 256,
                                   virtual=True)
            self._chips[chip.toString()] = chip
            #connect it to its predefined neighbour
            connected_chip_coords = virtual_chip.connected_chip_coords
            real_chip = self.get_chip(connected_chip_coords['x'],
                                      connected_chip_coords['y'])
            real_chips_router = real_chip.router
            link_id = virtual_chip.connected_chip_edge
            new_link = {'x': coords['x'],
                        'y': coords['y'],
                        '16bit': 256,
                        'object': chip.router}
            if link_id in real_chips_router.linksdownlist:
                real_chips_router.linksdownlist.remove(link_id)
            else:
                raise exceptions.PacmanException("connecting an external device "
                                                 "to a up link is not currently "
                                                 "supported in pacman103")
            real_chips_router.neighbourlist[link_id] = new_link
            #connect and update the fake routers neaighbour lists
            new_link_id = 0
            #new link has to be the opposite direction to the orginal
            if link_id == 0:
                new_link_id = 3
            elif link_id == 1:
                new_link_id = 4
            elif link_id == 2:
                new_link_id = 5
            elif link_id == 3:
                new_link_id = 0
            elif link_id == 4:
                new_link_id = 1
            elif link_id == 5:
                new_link_id = 2
            new_link = {'x': connected_chip_coords['x'],
                        'y': connected_chip_coords['y'],
                        '16bit': 256,
                        'object': real_chips_router}
            fake_chips_router = chip.router
            fake_chips_router.linksuplist.append(new_link_id)
            for index in range(6):
                if index == new_link_id:
                    fake_chips_router.neighbourlist.append(new_link)
                else:
                    fake_chips_router.neighbourlist.append(None)
                    fake_chips_router.linksdownlist.append(index)



    '''
    determines the routing of the board
    '''
    def determine_board_routing(self, hostname, conn):
        for xx in range(self.x_dim):
            for yy in range(self.y_dim):
                if self.chip_exists_at(xx, yy):
                    chipid = self.get_chip(xx, yy)
                    # Read the link status registers.
                    conn.select(xx, yy, 0)
                    linkraw = int(numpy.fromstring(
                        conn.memory_calls.read_mem(0xf5007f0c,
                                                   scamp.TYPE_BYTE, 1),
                        dtype=numpy.uint8))
                    for i in range(6):
                        if (linkraw >> i) & 0x1:
                            attachedcoord = \
                                int(numpy.fromstring(
                                    Machine.read_link_word(0xf5007f00, i, conn),
                                    dtype=numpy.uint32) & 0x0000FFFF)
                            attached_x = attachedcoord / 256
                            attached_y = attachedcoord % 256
                            if ((attached_x < self.x_dim) and
                                    (attached_y < self.y_dim) and
                                    self.chip_exists_at(attached_x, attached_y)):
                                # sanity check the neighbouring
                                # coordinates, exclude whackiness
                                chipid.router.neighbourlist.append({'x': attached_x,
                                                                    'y': attached_y,
                                                                    '16bit': attachedcoord,
                                                                    'object': None})
                                chipid.router.linksuplist.append(i)
                            else:
                                chipid.router.linksdownlist.append(i)
                                chipid.router.neighbourlist.append(None)
                        else:
                            chipid.router.linksdownlist.append(i)
                            chipid.router.neighbourlist.append(None)
                            # links to the neighbouring router objects are
                            # added in a second pass later

        # now to map the links to the neighbouring chips (a second pass
        # of the data only, no extra chip querying)
        for xx in range(self.x_dim):
            for yy in range(self.y_dim):
                if self.chip_exists_at(xx, yy):
                    chipid = self.get_chip(xx, yy)
                    if chipid != None:
                        # only when (xx,yy) chip exists loop over the links
                        for link in range(6):
                            if chipid.router.neighbourlist[link] is not None:
                                linked_chip = \
                                    self.get_chip(
                                        chipid.router.neighbourlist[link]['x'],
                                        chipid.router.neighbourlist[link]['y'])
                                self.link_count += 1
                                chipid.router.neighbourlist[link]['object'] = \
                                    linked_chip.router
                                #add the neighbour object list[0-5] with the
                                #  target router object
        print "Dynamic discovery complete. ", len(self.get_processors()), \
            "available app cores and", self.link_count / 2, "active links!"

        # links are divided by 2 as there are 2 ends to each link!

    def get_boards(self):
        """
        Returns a list of the boards constituting the machine.

        :returns: list of :py:object:`pacman103.lib.lib_machine.board` objects.
        """
        return self.boards

    def get_coords_of_all_chips(self):
        coords = list()
        for key in self._chips.keys():
            chip = self._chips[key]
            coords.append({'x': chip.x, 'y': chip.y})
        return coords

    '''
    method to return a list of chips USE AT YOUR PERIL
    list is un-ordered
    '''
    def get_chips_as_list(self):
        return self._chips.values()


    '''
    returns the chip defined by x and y, or raises an exception
    '''

    def get_chip(self, x, y):
        if self.chip_exists_at(x, y):
            return self._chips["{}:{}".format(x, y)]
        else:
            raise exceptions.PacmanException("no chip with coords "
                                             "{}:{}".format(x, y))

    '''
    checks that a chip exists in the dict
    '''

    def chip_exists_at(self, x, y):
        if "{}:{}".format(x, y) in self._chips:
            return True
        else:
            return False

    '''
    returns the processor defined by x,y,p in the chip or raises an exception
    '''

    def get_processor(self, x, y, p):
        return self._chips["{}:{}".format(x, y)].get_processor(p)

    '''
    returns a list of all the processors in the machine, no order is assumed
    '''

    def get_processors(self):
        pro_list = list()
        for key, chip in self._chips.items():
            if not chip.is_virtual():
                for pro in chip.get_processors():
                    pro_list.append(pro)
        return pro_list


    @staticmethod
    def read_link_word(start_addr, linkid, conn):
        """
        Reads data from a neighbouring chip over that link

        :param int start_addr: address to start reading from (type is always a 32-bit word!)
        :param int linkid:     which link to use, i.e. 0:E, 1: NE, 2:N, 3:W, 4:SW, 5:S
        :returns:              string containing the data read
        :raises:               SCPError

        """

        msg = SCPMessage(cmd_rc=scamp.CMD_LINK_READ)

        # confirm the data size is aligned to the appropriate boundary
        #self._check_size_alignment (type, size)

        # initialise tracker variables
        addr = start_addr
        buf = ''
        read_size = 4

        # read all the data
        while (addr - start_addr) < read_size:
            # build up the packet as follows:
            #   arg1 = start address
            #   arg2 = chunk length
            #   arg3 = element size
            msg.arg1 = addr
            msg.arg2 = min(read_size, scamp.SDP_DATA_SIZE)
            msg.arg3 = linkid
            resp = conn.conn.send_scp_msg(msg)

            # add the data to the buffer and update the tracker variables
            buf += resp.data
            addr += len(resp.data)
            read_size -= len(resp.data)

        # return the (hopefully valid) data buffer requested
        return buf

    def remove_downed_cores(self):
        '''
        removes a collection of processors from the list defined in
        pacman.cfg
        '''
        downed_cores = str(conf.config.get("Machine", "down_cores"))
        if downed_cores != "None":
            downed_cores_split = downed_cores.split(":")
            for downed_core in downed_cores_split:
                coords = downed_core.split(",")
                chip = self.get_chip(int(coords[0]), int(coords[1]))
                chip.remove_processor(int(coords[2]))


    def remove_downed_chips(self):
        '''
        removes a chip and its corrasponding processors from the list defined in
        pacman.cfg
        '''
        downed_chips = str(conf.config.get("Machine", "down_chips"))
        logger.debug("Down chips = {}".format(downed_chips))
        if downed_chips != "None":
            downed_chips_split = downed_chips.split(":")
            for downed_chip in downed_chips_split:
                coords = downed_chip.split(",")
                del self._chips["{}:{}".format(coords[0], coords[1])]
