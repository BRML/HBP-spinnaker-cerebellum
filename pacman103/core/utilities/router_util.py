"""
Python file that outputs files for debuging routing using graphviz.
"""

import os
from pacman103.core.utilities.machine_utils import MachineUtil

class RouterUtil(MachineUtil):

    def __init__(self, new_output_folder):
        super(RouterUtil, self).__init__(new_output_folder)

    @staticmethod
    def output_routing_weight(self, routing_dijkstra_tables, machine, routing_file_name="routingFile",
                              graph_label="routing"):
        #create labels
        labels = dict()
        #write data for each chip
        for key in routing_dijkstra_tables.keys():
            bits = key.split(":")
            labels[key] = routing_dijkstra_tables[key]["lowest cost"]
        #call the machine version of utils to output the machien
        # with these labels and files

        # SD 14/1/14: Removed this to prevent appearance of error
        #  messages during routing phase:
        self.output_machine(self, labels, machine,
                            machine_file_name=routing_file_name,
                            graph_label=graph_label,
                            show_cores=False)
