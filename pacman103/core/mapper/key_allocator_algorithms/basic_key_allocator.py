__author__ = 'stokesa6'
import logging
from pacman103.lib.machine.router import Router
logger = logging.getLogger( __name__ )

class BasicKeyAllocator(object):

    def __init__(self, dao):
        self.dao = dao

    '''
    starts the allocation fo keys process
    '''
    def allocate_keys(self):
         logger.info("* Running key allocator *")
         subverts = self.dao.get_subvertices()
         self.dao.inverseMap = dict()
         self.allocate_raw(subverts)

    '''
    takes each subvert and takes its outgoing edges and gives each one a key
    '''
    def allocate_raw(self, subverts):
        for subvert in subverts:
            for subedge in subvert.out_subedges:
                key, mask = subvert.vertex.generate_routing_info(subedge)
                key_mask_combo = self.get_key_mask_combo(key, mask)
                subedge.key_mask_combo = key_mask_combo
                subedge.key = key
                subedge.mask = mask
                # store the inverse for future use
                self.dao.inverseMap[key_mask_combo] = list()
                self.dao.inverseMap[key_mask_combo].append(subedge)
                #check for storage of masks
                self.check_masks(subedge.mask, key)

    '''
    updates the used mask store based on if its alresady been used
    '''
    def check_masks(self, new_mask, key):
        if new_mask not in self.dao.used_masks:
            self.dao.used_masks[new_mask] = list()
        #add to list (newly created or otherwise)
        self.dao.used_masks[new_mask].append(key)

    '''
    generates a key-mask combo based off the key and mask
    '''
    def get_key_mask_combo(self, key, mask):
        combo = key & mask
        return combo

