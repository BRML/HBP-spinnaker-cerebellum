__author__ = 'stokesa6'

import logging
logger = logging.getLogger(__name__)

class InverseMapper(object):

    @staticmethod
    def build_inverse_map(dao):
        """
        Constructs a 3-D map with one entry per core in the machine. Each entry
        provides a reference to the source vertex that is mapped to that core and
        the sub-portion therein (if appropriate). This information is pickled and
        passed out to another program that processes messages leaving the machine
        during simulation, allowing the domain-oriented processing of these events.
        :param `pacman103.core.dao` dao:
            datastore containing machine and vertex objects.

        .. todo::
         * Complete this...
        """
        # Build empty list for one chip (to be copied as required):
        emptyList = list()
        for i in range(18):
            emptyList.append([])
        # Construct inverse-map:
        dao.buildInverseMap = list()
        for x in range(dao.machine.x_dim):
            thisColumnOfChips = list()
            for y in range(dao.machine.y_dim):
                mappedToThisChip = emptyList
                thisChip = dao.machine.get_chip(x, y)
                if thisChip:
                    for p in thisChip.processors:
                        if p.placement:
                            mySubVertex = p.placement.subvertex
                            myVertex = mySubVertex.vertex
                            myLoAtom = mySubVertex.lo_atom
                            myHiAtom = mySubVertex.hi_atom
                            myVertexLabel = mySubVertex.vertex.label
                            mappedToThisChip[p.idx] = [myVertexLabel, myHiAtom, myLoAtom, myVertex]
                # Append list for this chip to the array:
                thisColumnOfChips.append(mappedToThisChip)
            # Append infor for this column of chips to the Inverse Map:
            dao.buildInverseMap.append(thisColumnOfChips)

        logger.debug("*** Inverse map constructed ***")
        dao.done_inverse_mapper = True
