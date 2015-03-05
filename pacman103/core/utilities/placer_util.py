"""
Python file that outputs files for debuging routing using graphviz.
"""

import os
from pacman103.core.utilities.machine_utils import MachineUtil

class PlacerUtil(MachineUtil):

    def __init__(self, new_output_folder=None):
        super(PlacerUtil, self).__init__(new_output_folder)


    @staticmethod
    def output_placements(self, machine, routing_file_name="placementFile", graph_label="placement"):
         #create labels
        labels = dict()
        #write data for each chip
        coords = machine.get_x_and_y_coords_of_all_chips()
        for chip in coords:
            x = chip['x']
            y = chip['y']
            labels[(x, y)] = routing_dijkstra_tables[x][y]["lowest cost"]
        #call the machine version of utils to output the machien with these labels and files
        self.output_machine(self, labels, machine, machine_file_name=routing_file_name, graph_label=graph_label)
