import os
import datetime
import shutil
from pacman103.lib import graph
from pacman103.lib.machine import machine
from pacman103.store import machines
from pacman103.core import data_spec_executor, exceptions

import time
import logging
logger = logging.getLogger(__name__)

class DAO( object ):
    """
    A DAO (Data Access Object, or *datastore*) is instantiated by a
    :py:func:`pacman103.core.control.Controller` object in order to store
    references to objects. In particular, the front-end represents the input
    model as :py:class:`pacman103.lib.graph.Vertex` and
    :py:class:`pacman103.lib.graph.Edge` objects, references to which are
    stored in two lists in the datastore; these are then read out by the
    partitioning, placement and routing stages, which generate further objects,
    references to which are placed in the datastore; ultimately, these
    references are read out to create data structures for the simulation on
    SpiNNaker. The datastore also instantiates and stores a reference to a
    description of the target machine onto which the front-end input is mapped.

    Note that "datastore" is something of a misnomer. In keeping with Python's
    broader object-handling methodology, the datastore stores only references to
    other objects, not the actual objects themselves. Thus, anyone with a
    reference to an object "in the datastore" can modify that object without any
    interaction with the datastore.

    :param module front_end:
        reference to the front-end module that instantiated this controller
    :param string hostname:
        hostname of the SpiNNaker machine on which the simulation is to be
        run.
    """
    time_of_compilation = None
    app_id = 30

    def __init__(self, front_end, hostname = None, output_folder = None):
        # Store reference to the front-end module
        self.front_end = front_end

        # Generate and store a machine object
        self.machine = None
        if not hostname is None:
            self.set_hostname( hostname )

        # Make lists for the front-end to append model elements to
        self.vertices = list()
        self.edges = list()

        # Make lists for data that will be created by successive PACMAN stages
        self.subvertices = list()
        self.subedges = list()
        self.iptags = list()
        self.placements = list()
        self.routings = list()
        self.inverseMap = None
        self.used_masks = dict()
        self.appPacketMonitorVertex = None
        self.dss = list()
        self.es = list()
        self.memMaps = dict()
        self.specExecutor = data_spec_executor.SpecExecutor()
        self.useHostBasedSpecExecutor = True
        self.rngs = dict()
        self.randDists = dict()
        self.writeTextSpecs = True
        self.writeBinarySpecs = True
        self.executable_targets = list()
        self.load_targets = list()
        self.mem_write_targets = list()
        # variables for pickle and depickling
        DAO.time_of_compilation = datetime.datetime.now()
        DAO.time_of_compilation = str(self.time_of_compilation.date()) + "-" + \
                                  str(self.time_of_compilation.hour) + "-" + \
                                  str(self.time_of_compilation.minute) + "-" + \
                                  str(self.time_of_compilation.second) #+ "-"# + \
                               #   str(self.time_of_compilation.microsecond)
        self.vertex_count = 0
        self.edge_count = 0


       # self.compilation_time =
        self.run_time = None
        self.time_scale_factor = 1
        self.machineTimeStep = 1000 #Interval between neuron updates, in u-seconds

        #flags for mapper
        self.done_partitioner = False
        self.done_placer = False
        self.done_router = False
        self.done_inverse_mapper = False
        self.done_key_allocation = False

        #flags for transciever
        self.load_apps = True
        self.run_apps = True
        self.has_ran = False

        #flag for moving latest to non-latest folders
        self.moved_already = False

        #master population data stores for after running for faster retrievals
        self.master_population_tables = dict()



    def set_hostname( self, hostname ):
        #determine how many vertexes are virtual
        virtual_vertexs = list()
        for vertex in self.vertices:
            if vertex.virtual:
                self.check_if_vertex_needs_merging(vertex, virtual_vertexs)
        # Generate and store a machine object
        if not hostname in machines.machines:
            warningStr =  "Structure of target SpiNNaker machine not known.\n"
            warningStr += "Interrogating machine for details of structure." 
            logger.warning(warningStr)
            self.machine = machine.Machine(hostname, type="dynamic",
                                           virtual_verts=virtual_vertexs)
        else:
            description = machines.machines[hostname]
            description['virtual_verts'] = virtual_vertexs
            self.machine = machine.Machine(**description)

    def check_if_vertex_needs_merging(self, vertex, virtual_vertexs):
        #for each virtual vertex, merge entries which have the same chip ids
        merged = False
        index = 0
        while not merged and index <= len(virtual_vertexs) -1:
            compare = virtual_vertexs[index]
            compare_coords = compare.virtual_chip_coords
            compare_con_coords = compare.connected_chip_coords
            if (compare_coords['x'] == vertex.virtual_chip_coords['x'] and
                compare_coords['y'] == vertex.virtual_chip_coords['y']):
                if (compare_con_coords['x'] == vertex.connected_chip_coords['x'] and
                    compare_con_coords['y'] == vertex.connected_chip_coords['y'] and
                    compare.connected_chip_edge == vertex.connected_chip_edge):
                    merged = True
                else:
                    raise exceptions.PacmanException("cannot merge entries as "
                                                     "the connected corods and "
                                                     "edge are not identicle")

            elif (compare_con_coords['x'] == vertex.connected_chip_coords['x'] and
                    compare_con_coords['y'] == vertex.connected_chip_coords['y'] and
                    compare.connected_chip_edge == vertex.connected_chip_edge):
                raise exceptions.PacmanException("cannot merge entries as "
                                                 "the connected corods and edge"
                                                 "are identicle to some other "
                                                 "virtual chip with different "
                                                 "coords")
            index += 1
        if not merged:
            virtual_vertexs.append(vertex)

    def add_vertex(self, vertex):
        """
        Adds a vertex object to the datastore.

        :param `pacman103.lib.graph.Vertex` vertex:
            Vertex object to be added.
        """
        if not isinstance(vertex, graph.Vertex):
            raise TypeError("Can only add subclasses of "
                            "pacman103.lib.graph.Vertex as vertices. ")
        self.vertices.append(vertex)
        return len(self.vertices) - 1




    def add_edge(self, edge):
        """
        Adds an edge object to the datastore.

        :param `pacman103.lib.graph.Edge` edge:
            Edge object to be added.
        """
        if not isinstance( edge, graph.Edge ):
            raise TypeError( "Can only add subclasses of " \
                             "pacman103.lib.graph.Edge as edges. " )
        self.edges.append(edge)

    def add_rng(self, rngIndex, rngInfo):
        """
        Adds a random number generator object to the datastore.
        """
        self.rngs[rngIndex] = rngInfo

    def add_randomDistribution(self, distIndex, distInfo):
        """
        Adds a random distribution object to the datastore.
        """
        self.randomDists[distIndex] = distInfo

    def get_executable_targets(self):
        """
        Gets all executable targets.

        :returns:
            list of :py:class:`pacman103.lib.lib_map.ExecutableTarget`
            instances.
        """
        return self.executable_targets


    def get_front_end(self):
        """
        Get the front-end module.

        :returns: Python ``module`` of the front end.
        """
        return self.front_end


    def get_load_targets(self):
        """
        Gets all load targets.

        :returns:
            list of :py:class:`pacman103.lib.lib_map.LoadTarget` instances.
        """
        return self.load_targets


    def get_mem_write_targets(self):
        """
        Gets all poke mem-write targets.

        :returns:
            list of :py:class:`pacman103.lib.lib_map.MemWriteTarget` instances.
        """
        return self.mem_write_targets


    def get_machine(self):
        """
        Get the machine object.

        :returns: :py:class:`pacman103.lib.machine.machine.Machine` instance.
        """
        return self.machine


    def get_subedges(self):
        """
        Gets all subedges.

        :returns:
            list of :py:class:`pacman103.lib.graph.Subedge` instances.
        """
        return self.subedges


    def get_subvertices(self):
        """
        Gets all subvertices.

        :returns:
            list of :py:class:`pacman103.lib.graph.Subvertex` instances.
        """
        return self.subvertices


    def get_vertices(self):
        """
        Gets all vertices.

        :returns:
            list of :py:class:`pacman103.lib.graph.Vertex` instances.
        """
        return self.vertices

    def get_edges(self):
        """
        Gets all edges.
        :returns:
            list of :py:class:'pacman103.lib.graph.Edge' instances.
        """
        return self.edges


    def set_executable_targets(self, executable_targets):
        """
        Sets all executable targets.

        :params:
            list of :py:class:`pacman103.lib.lib_map.ExecutableTarget`
            instances.
        """
        self.executable_targets = executable_targets


    def set_load_targets(self, load_targets):
        """
        Sets all load targets.

        :params:
            list of :py:class:`pacman103.lib.lib_map.LoadTarget` instances.
        """
        self.load_targets = load_targets


    def set_mem_write_targets(self, mem_write_targets):
        """
        Sets all individual memory write targets. (pokes)

        :params:
            list of :py:class:`pacman103.lib.lib_map.MemWriteTarget` instances.
        """
        self.mem_write_targets = mem_write_targets


    def set_subedges(self, subedges):
        """
        Sets all subedges.

        :params:
            list of :py:class:`pacman103.lib.graph.Subedge` instances.
        """
        self.subedges = subedges


    def set_subvertices(self, subvertices):
        """
        Sets all subvertices.

        :params:
            list of :py:class:`pacman103.lib.graph.Subvertex` instances.
        """
        self.subvertices = subvertices

    def set_placements(self, placements):
        """
        Sets all placements.

        :params:
            list of :py:class:`pacman103.lib.map.placement` instances.
        """
        self.placements = placements

    def add_iptag(self, iptag):
        """
        supports adding iptags to the dao for use by the transceiver
        """
        self.iptags.append(iptag)

    def get_iptags(self):
        return self.iptags

    @staticmethod
    def get_binaries_directory(reload_time=None):
        """
        Gets a string representing the directory where the binaries are located, 
        extracted from the parent directory of the pacman103 python module                

        Code adapted from 
        http://stackoverflow.com/questions/6015721/getting-a-specific-parent-folder-with-python
        """
        components = os.path.abspath(machine.__file__).split(os.sep)
        directory = os.path.abspath(os.path.join(os.sep,
                 *components[1:components.index("pacman103")]))
        binaries_folder = os.path.join(directory,  "output_binaries")
        if not os.path.exists(binaries_folder):
                os.makedirs(binaries_folder)
        if reload_time is None:
            app_specific_binary_folder =\
                os.path.join(binaries_folder,
                             "app_{}_{}".format(DAO.app_id,
                                                DAO.time_of_compilation))
        else:
           app_specific_binary_folder =\
                os.path.join(binaries_folder,
                             "app_{}_{}".format(DAO.app_id, reload_time))
        return app_specific_binary_folder


    def get_reports_directory(self, subdirectory = None):
        """
        Gets a string representing the directory where the reportsare located, 
        extracted from the parent directory of the pacman103 python module                

        Code adapted from 
        http://stackoverflow.com/questions/6015721/getting-a-specific-parent-folder-with-python
        """

        components = os.path.abspath(machine.__file__).split(os.sep)
        directory = os.path.abspath(os.path.join(os.sep,
                 *components[1:components.index("pacman103")]))
        #global reports folder
        directory = os.path.join(directory, 'reports')
        if not os.path.exists(directory):
            os.makedirs(directory)

       # app specific folder
        app_specific_report_folder = os.path.join(directory, "latest")
        if not os.path.exists(app_specific_report_folder):
            os.makedirs(app_specific_report_folder)
            #store timestamp in latest/time_stamp
            app_name_file = os.path.join(app_specific_report_folder,
                                         "time_stamp")
            writer = open(app_name_file, "w")
            writer.writelines("app_{}_{}".format(DAO.app_id,
                                                 DAO.time_of_compilation))
            writer.flush()
            writer.close()
            self.moved_already = True
        else:
            if not self.moved_already:
                #rename old latest and move contents
                app_name_file = os.path.join(app_specific_report_folder,
                                             "time_stamp")
                time_stamp_in = open(app_name_file, "r")
                time_stamp_in_string = time_stamp_in.readline()
                time_stamp_in.close()
                new_app_folder = os.path.join(directory,
                                              time_stamp_in_string)
                os.makedirs(new_app_folder)
                list_of_files = os.listdir(app_specific_report_folder)
                for file_to_move in list_of_files:
                    file_path = os.path.join(app_specific_report_folder,
                                             file_to_move)
                    shutil.move(file_path, new_app_folder)
                #store timestamp in latest/time_stamp
                writer = open(app_name_file, "w")
                writer.writelines("app_{}_{}".format(DAO.app_id,
                                                     DAO.time_of_compilation))
                writer.flush()
                writer.close()
                self.moved_already = True

        #sub directory folder
        if subdirectory is not None:
            directory = os.path.join(app_specific_report_folder, subdirectory)
        else:
            directory = app_specific_report_folder
        #check if directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def write_running_msg(self):
        rep_dir = self.get_reports_directory()
        running_file = os.path.join(rep_dir,"app_running")
        writer = open(running_file,"w")
        writer.write(format(time.time(),".4f")+"\n")
        writer.close()
        
    @staticmethod
    def get_common_binaries_directory():
        '''
        Gets a string representing the directory where the common binaries are located,
        extracted from the parent directory of the pacman103 python module
        '''
        components = os.path.abspath(machine.__file__).split(os.sep)
        directory = os.path.abspath(os.path.join(os.sep,
                 *components[1:components.index("pacman103")]))
        binaries_folder = os.path.join(directory,  "binaries")
        return binaries_folder
