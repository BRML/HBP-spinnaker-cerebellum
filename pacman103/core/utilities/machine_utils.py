"""
Python file that outputs files for debuging routing using graphviz.
"""

import os
from pacman103 import conf

class MachineUtil(object):

    def __init__(self, new_output_folder):
        self.output_folder = new_output_folder
        if not type( self.output_folder ) is str:
            raise Exception( self.output_folder )

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # SD 14/1/14: Remoed this to prvent extraneous output:
        # print self.output_folder

    @staticmethod
    def empty_dir(self, output_folder):
        for directory_file in os.listdir(output_folder):
                if os.path.isdir(output_folder + os.sep + directory_file):
                    self.empty_dir(self, output_folder + os.sep + directory_file)
                else:
                    os.remove(output_folder+ os.sep + directory_file)

    @staticmethod
    def output_machine(self, labels, machine, machine_file_name="routingFile", two_way_edges=False,
                       edge_labels=None, graph_label="machine", show_cores=True):
        #open file to write data to
        file_name = self.output_folder + os.sep + machine_file_name
        output = open(file_name + ".dot", "w")
        #write blurb at top
        output.writelines("digraph \"" + graph_label + "\" { \n size = \"8.5,11\"; \n" +
                          "rankdir=\"BT\"; \n label=\"" + graph_label + "\"; \n \n")

        #make cluster
        output.writelines("subgraph cluster_1 { edge[constraint=false];\n label=\"\" \n")

        if show_cores:
            self.write_with_cores(self, machine, output, labels, two_way_edges, edge_labels)
        else:
            self.write_without_cores(self, machine, output, labels, two_way_edges, edge_labels)


        #write lower blurb
        output.writelines("}\n}\n")
        output.flush()
        output.close()
        #run this command to compile dot files correctly
        # dot -Kfdp -n -Tpng -o routingFile.png routingFile.dot
        # eps seems to be easier to read for 48 chip boards
        #commandline = "dot -Kfdp -n -Tpng -o " + file_name + ".png " + file_name + ".dot"
        commandline = "dot -Kfdp -n -Teps -o " + file_name + ".eps " + file_name + ".dot"
        os.system(commandline)
        commandline = "dot -Kfdp -n -Tpng -o " + file_name + ".png " + file_name + ".dot"
        os.system(commandline)


    @staticmethod
    def write_with_cores(self, machine, output, labels, two_way_edges, edge_labels):
        #write data for each chip
        for x in range(machine.x_dim):
            for y in range(machine.y_dim):
                chip_id = self.determine_chip_id(x, y, machine.x_dim)
                output.writelines("subgraph cluster_" + str(x) + "_" + str(y) +
                                  "{\n pos=\"" + str(6*x) + "," + str(6*y) + "!\"\n label=\"(" + str(x) +
                                  ", " + str(y) + ")\"\n rank=\"same\";\n")
                for processor in machine.get_chip(x, y).get_processors():
                    inner_x, inner_y = self.processor_position(processor.idx)
                    output.writelines("\"" + str(x) + "_" + str(y) + "_" + str(processor.idx) +
                                      "\" [ fontsize=9 label = \"(" + str(x) + "_" + str(y) + "_" + str(processor.idx) +
                                      ")" +
                                     # labels[(x, y, processor.idx)] +
                                      "\" pos=\"" + str(6*x + inner_x) + "," + str(6*y + inner_y) +
                                      "!\" shape=square]; \n")
                output.writelines("} \n")
        #write data for each edge
        for x in range(machine.x_dim):
            for y in range(machine.y_dim):
                added_links = list()
                for link in machine.get_chip(x, y).router.neighbourlist:
                    if link is not None:
                        new_chip_id = self.determine_chip_id(link['x'], link['y'], machine.x_dim)
                        chip_id = self.determine_chip_id(x, y, machine.x_dim)
                        coords = (chip_id, new_chip_id)
                        if two_way_edges or (not two_way_edges and coords not in added_links):
                            #print coords
                            added_links.append((new_chip_id, chip_id))
                            added_links.append((chip_id, new_chip_id))
                            if edge_labels is not None:
                                output.writelines("\"cluster_" + str(x) + "_" + str(y) + "\"-> \"cluster_" + str(link['x']) + "_" +
                                                  str(link['y']) + "\" [ fontsize=9 label = \"" + edge_labels[x][y] + "\" dir=none ]\n")
                            else:
                                output.writelines("\"cluster_" + str(x) + "_" + str(y) + "\"-> \"cluster_" + str(link['x']) + "_" +
                                                  str(link['y']) + "\" [ fontsize=9 label = \" \" dir=none ]\n")





    @staticmethod
    def processor_position(phyid):
        if phyid == 0:
            return 0, 3
        elif phyid == 1:
            return 3, 3
        elif phyid == 2:
            return 0, 0
        elif phyid == 3:
            return 3, 0
        elif phyid == 4:
            return 0, 4
        elif phyid == 5:
            return 3, 4
        elif phyid == 6:
            return 0, 1
        elif phyid == 7:
            return 3, 1
        elif phyid == 8:
            return 1, 3
        elif phyid == 9:
            return 2, 3
        elif phyid == 10:
            return 1, 0
        elif phyid == 11:
            return 2, 0
        elif phyid == 12:
            return 1, 4
        elif phyid == 13:
            return 2, 4
        elif phyid == 14:
            return 1, 1
        elif phyid == 15:
            return 2, 1
        elif phyid == 16:
            return 0, 2
        else:
            return 3, 2







    @staticmethod
    def write_without_cores(self, machine, output, labels, two_way_edges, edge_labels):
        #write data for each chip
        for coord in machine.get_coords_of_all_chips():
            x, y = coord['x'], coord['y']
            chip_id = self.determine_chip_id(x, y, machine.x_dim)
            output.writelines("\"" + str(chip_id) + "\" [fontsize=9 label = \"(" + str(x) + "," + str(y) +
                              ") "+ str(labels["{}:{}".format(x, y)]) +
                              "\" pos=\"" + str(x*2) + "," + str(y*2) + "!\" shape=rectangle]; \n")


        #write each edge data foe ech chip
        added_links = list()
        for coords in machine.get_coords_of_all_chips():
            x,y = coords['x'], coords['y']
            for link in machine.get_chip(x,y).router.neighbourlist:
                if link is not None:
                    new_chip_id = self.determine_chip_id(link['x'], link['y'], machine.x_dim)
                    chip_id = self.determine_chip_id(x, y, machine.x_dim)
                    coords = (chip_id, new_chip_id)
                    if two_way_edges or (not two_way_edges and coords not in added_links):
                        #print coords
                        added_links.append((new_chip_id, chip_id))
                        added_links.append((chip_id, new_chip_id))
                        if edge_labels is not None:
                            output.writelines("\"" + str(chip_id) + "\"->\"" + str(new_chip_id) +
                                              "\" [fontsize=9 label = \"" + edge_labels[x][y] + "\" dir=none ]; \n")
                        else:
                            output.writelines("\"" + str(chip_id) + "\"->\"" + str(new_chip_id) +
                                              "\" [fontsize=9 label = \" \" dir=none ]; \n")





    @staticmethod
    def determine_chip_id(x, y, max_x):
        if y == 0:
            return x
        else:
            ynew = y * max_x
            return ynew + x
