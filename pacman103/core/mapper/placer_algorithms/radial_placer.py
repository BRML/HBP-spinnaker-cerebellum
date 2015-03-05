
import logging
logger = logging.getLogger(__name__)

from pacman103.core.mapper.placer_algorithms.basic_placer import \
    BasicPlacer, PlacementChip, SDRAM_AVAILABLE, CPU_AVAILABLE, DTCM_AVAILABLE

class RadialPlacer(BasicPlacer):
    
    def get_chips(self):
        
        processors_new_order = list()
        chips_to_check = list()

        for coord in self.dao.get_machine().get_coords_of_all_chips():
            x, y = coord['x'], coord['y']
            chip = self.dao.machine.get_chip(x, y)
            if not chip.is_virtual():
                chips_to_check.append(chip)

        #start at 0,0 going out from its outbound edges till all chips checked
        current_chip_list_to_check = list()
        current_chip_list_to_check.append(self.dao.machine.get_chip(0,0))
        while len(chips_to_check) != 0:
            next_chip_list_to_check = list()
            for chip in current_chip_list_to_check:
                if (chips_to_check.count(chip) != 0):
                    processors_new_order.append(
                            PlacementChip(chip.boardid, chip.x, chip.y, 
                                    chip.get_processors(), SDRAM_AVAILABLE,
                                    CPU_AVAILABLE, DTCM_AVAILABLE))
                    chips_to_check.remove(chip)
                    for neabour_data in chip.router.get_neighbours():
                        if(neabour_data is not None):
                            neaubour_chip = \
                                self.dao.machine.get_chip(neabour_data['x'],
                                                          neabour_data['y'])
                            if(chips_to_check.count(neaubour_chip) == 1 and
                               next_chip_list_to_check.count(neaubour_chip) == 0):
                                next_chip_list_to_check.append(neaubour_chip)
            current_chip_list_to_check = next_chip_list_to_check
            
        return processors_new_order



