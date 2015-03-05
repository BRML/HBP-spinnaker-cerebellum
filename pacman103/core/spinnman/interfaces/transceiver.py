import numpy
import struct
import time

from pacman103.core.spinnman.scp.scp_connection import SCPConnection
from pacman103.core.spinnman.interfaces.transceiver_tools.app_calls import AppCalls
from pacman103.core.spinnman.interfaces.transceiver_tools.memory_calls import MemoryCalls
from pacman103.core.spinnman.interfaces.transceiver_tools.packet_calls import PacketCalls
from pacman103.core.spinnman.interfaces.transceiver_tools.utility import Utility
from pacman103.core.spinnman.scp import scamp
from pacman103.core.spinnman.spinnman_utilities import SpinnmanUtilities
from pacman103.core.spinnman.scp import boot
from pacman103 import conf
from pacman103.core import exceptions
import subprocess
import socket
import sys
import platform


import logging
import os
import logging
logger = logging.getLogger(__name__)

class Transceiver(object):
    """
    A Transceiver is instantiated by a
    :py:func:`pacman103.pacman.control.Controller` object in order to communicate
    with a SpiNNaker board. The Transceiver class is simply a wrapper around the
    :py:mod:`pacman103.scp` module, which does the actual interfaces over
    Ethernet. An instance of the class maintains a SCP connection to a machine,
    through which all interfaces takes place.

    :param string hostname:
        hostname of the SpiNNaker machine on which the simulation is to be run.
    """

    def __init__(self, hostname, port=17893):
        self.conn = SCPConnection(hostname, port)
        self.app_calls = AppCalls(self)
        self.memory_calls = MemoryCalls(self)
        self.packet_calls = PacketCalls(self)
        self._x = 0
        self._y = 0
        self.utility = None


    def read_memory(self, x, y, p, a, l, dtype):
        """
        Read memory from the SpiNNaker machine.

        :param int x: x-chip-coordinate.
        :param int y: y-chip-coordinate.
        :param int p: processor ID.
        :param int a: target load address.
        :param int l: length of data to read (bytes).
        :param numpy.dtype dtype:
            datatype of the returned numpy array (e.g. numpy.int32)

        :returns: numpy.ndarray containing the requested memory.
        """
        self.select(x, y, p)
        memory = self.memory_calls.read_mem(a, scamp.TYPE_WORD, l)
        memory = numpy.fromstring(memory, dtype=dtype)

        return memory


    def load_targets(self, dao):
        """
        Loads LoadTargets from the datastore and calls
        :py:func:`pacman103.pacman.transceiver.Transceiver.load_targets_raw`.
        """
        if conf.config.get("Reports", "write_reload_steps"):
            self.utility = SpinnmanUtilities(dao=dao)
        #check to see if the machine is contactable & loadable
        self.check_target_machine(dao.machine.hostname,
                                              dao.machine.y_dim,
                                              dao.machine.y_dim)

        # now get the data to load and then do it
        targets = dao.get_load_targets()
        self.load_targets_raw(targets)


    def load_targets_raw(self, targets):
        """
        Uses the SCP connection to load LoadTargets to the machine.

        :param list targets:
            list of :py:class:`pacman103.lib.lib_map.LoadTarget` instances.
        """
        for target in targets:
            if conf.config.get("Reports", "write_reload_steps"):
                self.utility.write_selects(target.x, target.y, target.p)
                self.utility.write_mem_from_file(target.address, scamp.TYPE_WORD,
                                                 target.filename)
            self.select(target.x, target.y, target.p)

            self.memory_calls.write_mem_from_file(target.address, scamp.TYPE_WORD,
                                                  target.filename)

    def load_targets_load(self, file_name):
        self.utility = SpinnmanUtilities(input_file=file_name)
        commands = self.utility.get_mem_writes_from_file()
        for index in range(0, len(commands), 2):
            self.select(int(commands[index]['x']), int(commands[index]['y']),
                        int(commands[index]['p']))
            self.memory_calls.write_mem_from_file(int(commands[index+1]['address']),
                                                  int(commands[index+1]['type_word']),
                                                  commands[index+1]['filename'])


    def load_write_mem(self, dao):
        """
        Loads WriteMemTargets from the datastore and calls
        :py:func:`pacman103.pacman.transceiver.Transceiver.load_write_mem_raw`.
        """
        targets = dao.get_mem_write_targets()
        self.load_write_mem_raw(targets)


    def load_write_mem_raw(self, targets):
        """
        Uses the SCP connection to load WriteMemTargets to the machine.

        :param list targets:
            list of :py:class:`pacman103.lib.lib_map.WriteMemTarget` instances.
        """
        for target in targets:
            if conf.config.get("Reports", "write_reload_steps"):
                self.utility.write_selects(target.x, target.y, target.p)
                self.utility.write_mem(target.address, scamp.TYPE_WORD,
                                       struct.pack("I", target.data))
            self.select(target.x, target.y, target.p)
            self.memory_calls.write_mem(target.address, scamp.TYPE_WORD,
                                        struct.pack("I", target.data))

    def load_write_mem_load(self, file_name):
        self.utility = SpinnmanUtilities(input_file=file_name)
        commands = self.utility.get_mem_writes()
        for index in range(0, len(commands), 2):
            self.select(int(commands[index]['x']), int(commands[index]['y']),
                        int(commands[index]['p']))
            self.memory_calls.write_mem(int(commands[index+1]['address']),
                                        int(commands[index+1]['type_word']),
                                        commands[index+1]['structure'])

    def reset_board(self):
        """
        TODO

        Implement to reset Spinn4 boards over SCP.
        """
        """
        #TODO check board is version 4 or greater
        scp.reset(kwargs['bmp'])
        time.sleep(5)
        scp.boot(hostname, '/home/tomxsharp/Thesis/spinnaker/tools/scamp-200.boot')#COMMENT ME
        time.sleep(2)
        self.txrx.conn.init_p2p_tables(self.dao.machine.x_dim, self.dao.machine.y_dim)
        self.txrx.conn.set_iptag(0, 'localhost', 17892)
        """
        pass


    def run(self, dao, app_id):
        """
        Loads ExecutableTargets from the datastore and calls
        :py:func:`pacman103.pacman.transceiver.Transceiver.run_raw`.
        """
        machine = dao.get_machine()
        targets = dao.get_executable_targets()
        iptags = dao.get_iptags()
        run_time = dao.run_time #TODO accessor method
        self.run_raw(machine, targets, run_time, app_id, iptags, dao)


    def run_raw(self, machine, targets, run_time, app_id, iptags, dao):
        """
        Uses the SCP connection to trigger simulation.

        :param `pacman103.lib.lib_machine.Machine` machine:
            machine to run the simulation on.
        :param list targets:
            list of :py:class:`pacman103.lib.lib_map.ExecutableTarget`
            instances.
        :param int run_time: run time of the simulation (milliseconds)
        """
        
        # Select monitor pacman on ethernet-adjacent chip
        self.select(0, 0)
        
        # Set IP tags
        for iptag in iptags:
            retries = 0
            while retries < 3:
                try:
                    logger.info("Setting up ip tag {} to {}:{}".format(
                                 iptag.tag, iptag.hostname, iptag.port))
                    self.conn.set_iptag(iptag.tag, iptag.hostname,
                                iptag.port)
                    retries = 3
                except Exception as e:
                    if retries == 3:
                        exceptions.SpinnManException("IPTags failed to be set "
                                                     "due to {}".
                                                     format(e.message))
                    retries += 1
                    time.sleep(0.1)
        
        total_processors = 0
        targets = self.organise_targets(targets)
        for key in targets.keys():
            chips = targets[key]
            core_mask = 0
            for chip in chips:
                processors = chips[chip]
                core_part_of_region = ""
                first = True
                for processor in processors:
                    core_mask += processor
                    if first:
                        core_part_of_region += "{}".format(processor)
                        first = False
                    else:
                        core_part_of_region += ",{}".format(processor)

                    total_processors += 1

                (x, y) = chip.split(",")
                region = Utility.calculate_region_id(int(x), int(y))

                if conf.config.get("Reports", "write_reload_steps"):
                    self.utility.write_app_load_command(key, region,
                                                        core_part_of_region,
                                                        app_id)

                self.app_calls.app_load(key, region, core_part_of_region, app_id)

                processors_ready = 0
                logger.debug("checking that the processors currently"
                             " flood filled are ready for future flood fills")
                while processors_ready < total_processors:
                    processors_ready = self.app_calls.app_signal(app_id,
                        scamp.SIGNAL_COUNT, scamp.PROCESSOR_SYNC0)
                    logger.debug("{} processors out of {} "
                         "processors are ready".format(processors_ready,
                         total_processors))

        logger.info("Waiting for application to finish loading")

        if conf.config.get("Reports", "write_reload_steps"):
                    self.utility.write_extra_data(run_time, total_processors)
                    self.utility.close()

        self.check_synco_and_run(total_processors, app_id, run_time, dao)


    def check_synco_and_run(self, total_processors, app_id, run_time, dao):
        '''
        checks that all processors have reached sync0 and runs the
        application for the given runtime
        '''
        processors_ready = 0
        while processors_ready < total_processors:
            processors_ready = self.app_calls.app_signal(app_id,
                                                         scamp.SIGNAL_COUNT,
                                                         scamp.PROCESSOR_SYNC0)
        logger.info("Starting application")
        self.app_calls.app_signal(app_id, scamp.SIGNAL_SYNC0)

        logger.info("Checking that the application has started")
        processors_running = self.app_calls.app_signal(app_id,
                                          scamp.SIGNAL_COUNT,
                                          scamp.PROCESSOR_RUN)
        if processors_running < total_processors:
            raise exceptions.SpinnManException("Only {} of {} processors "
                                               "started".format(processors_running,
                                                                total_processors))

        if run_time is not None:
            logger.info("Application started - waiting for it to stop")
            time.sleep(run_time / 1000.0)
            processors_not_finished = processors_ready
            while processors_not_finished != 0:
                processors_not_finished = self.app_calls.app_signal(app_id,
                                              scamp.SIGNAL_COUNT,
                                              scamp.PROCESSOR_RUN)
                processors_rte = self.app_calls.app_signal(app_id,
                                              scamp.SIGNAL_COUNT,
                                              scamp.PROCESSOR_RTE)
                if processors_rte > 0:
                    raise exceptions.SpinnManException("{} cores have gone into "
                                                       "a run time error state.".
                                                       format(processors_rte))


            processors_exited = self.app_calls.app_signal(app_id,
                                              scamp.SIGNAL_COUNT,
                                              scamp.PROCESSOR_EXIT)

            if processors_exited < total_processors:
                raise exceptions.\
                    SpinnManException("{} of the processors "
                                      "failed to exit successfully"
                                      .format(total_processors
                                              - processors_exited))

            logger.info("Application has run to completion")
            # update the dao holder so that stuff can be read from the SDRAM
            dao.has_ran = True
        else:
            logger.info("Application is set to run forever - PACMAN is exiting")
        retry_counts = self.conn.get_retries()
        logger.debug("Total retries on this run due to RC_TIMEOUT: {}, "
                + "RC_P2P_TIMEOUT: {}, RC_LEN: {}".format(retry_counts[0], 
                        retry_counts[1], retry_counts[2]))


    def run_load(self, utility_file):

        utility = SpinnmanUtilities(utility_file)
        run_time = utility.get_run_time()
        total_processors_of_app = utility.get_total_processors()
        app_loads = utility.get_app_loads()

        total_processors = 0
        app_id = None
        for app_load in app_loads:
            self.app_calls.app_load(app_load['key'], app_load['region'],
                                    app_load['core_part_of_region'],
                                    app_load['app_id'])
            app_id = app_load['app_id']
            processors_ready = 0

            logger.debug("checking that the processors currently"
                         " flood filled are ready for future flood fills")
            while processors_ready < total_processors:
                processors_ready = \
                    self.app_calls.app_signal(app_id, scamp.SIGNAL_COUNT,
                                              scamp.PROCESSOR_SYNC0)
                logger.debug("{} processors out of {} processors are "
                             "ready".format(processors_ready, total_processors))

        self.check_synco_and_run(total_processors_of_app, app_id, run_time)



    def organise_targets(self, targets):
        '''
        method that takes the targets and converts them into a list of chip scoped
        targets where each entry contains the chip
        '''
        organised_targets = dict()
        for target in targets:
            key = "{},{}".format(target.targets[0]['x'], target.targets[0]['y'])
            proc = target.targets[0]['p']
            if organised_targets.has_key(target.filename):
                chip_collection = organised_targets.get(target.filename)
                if key in chip_collection:
                    chip_collection[key].append(proc)
                else:
                    chip_collection[key] = [proc]
            else:
                #add with the chip definition
                chip_collection = dict()
                chip_collection[key] = [proc]
                organised_targets[target.filename] = chip_collection
        return organised_targets

    def check_target_machine(self, hostname, x, y):
        """
        This routine takes the requested dimension hints and the hostname of the machine,
            then checks that it is pingable on the network, has been booted and has physical
            dimensions that at least match the requested dimensions.

        :param int hostname:   address of the physical machine that we'll be using
        :param int x:          dimensions requested of the machine (may be smaller than the physical machine, but not bigger!)
        :param int y:          dimensions requested of the machine (may be smaller than the physical machine, but not bigger!)
        :returns:              xdims, and ydims which contain the physical dimensions detected in the machine
        :raises:               ExploreException

        """
        # check if machine is active and on the network
        pingtimeout=5
        # number of times to retry operations to wake up the board / ARP entries on the network
        while (pingtimeout):
            process = None
            if (platform.platform().lower().startswith("windows")):
                process = subprocess.Popen("ping -n 1 -w 1 " + hostname, shell=True, stdout=subprocess.PIPE)
            else:
                process = subprocess.Popen("ping -c 1 -W 1 " + hostname, shell=True, stdout=subprocess.PIPE)
            process.wait()
            if (process.returncode == 0):
                break
                # ping worked
            else:
                print "."
                pingtimeout-=1
                if (pingtimeout==0):
                    raise exceptions.ExploreException("EXPLORE ERROR: Cannot ping"
                                                       ,hostname,"- is it active on "
                                                       "the network?")



        # board booted
        conn = Transceiver(hostname, 17893)
        # open a connection to the board for probing with SCP packets
        bootedtimeout=5
        # number of times to retry operations to wake up the board / ARP entries on the network
        while (bootedtimeout):
            try:
                conn.select('root')
                version = conn.conn.version(retries=3)
                print version.desc
                break
            except socket.error:
                print "."
                bootedtimeout-=1
            except Exception:
                self.explore_a_reboot(hostname)


        # recover dimensions
        ydims = int(numpy.fromstring(conn.memory_calls.read_mem(0xf5007f02, scamp.TYPE_BYTE, 1), dtype=numpy.uint8))
        xdims = int(numpy.fromstring(conn.memory_calls.read_mem(0xf5007f03, scamp.TYPE_BYTE, 1), dtype=numpy.uint8))
        myString = "EXPLORE: found machine '%s' that is contactable," % hostname
        myString += " and has dimensions (x:%d, y:%d)" % (xdims, ydims)
        logger.debug(myString)
        if (xdims==0):
            errorString = "EXPLORE ERROR: '%s' is booted," % hostname
            errorString += " but x-dimension is returning zero!"
            raise exceptions.ExploreException(errorString)
        if (ydims==0):
            errorString = "EXPLORE ERROR: '%s' is booted," % hostname
            errorString += " but y-dimension is returning zero!"
            raise exceptions.ExploreException(errorString)
        if (y!=None or x!=None):
            # hints provided so better check them
            if (xdims<x or ydims<y):
                raise exceptions.ExploreException("EXPLORE ERROR: '", hostname,
                                                  "' the x and y hints supplied "
                                                  "are bigger than the actual "
                                                  "machine dimensions")


        return xdims,ydims


    def explore_a_reboot(self, hostname):
        if (conf.config.has_option("Machine", "tryReboot") and
            conf.config.getboolean("Machine", "tryReboot")):
                logger.info("cannot ping {}- will try to reboot board".format(hostname))
                version_number = conf.config.get("Machine", "version")
                if version_number is None or version_number == "None" or int(version_number) > 5:
                    raise exceptions.SpinnManException("version number is not defined in pacman.cfg. Please enter and retry")

                boot_file = self.checkfile("scamp-130.boot")
                struct_file = self.checkfile("sark-130.struct")
                config_file = self.checkfile("spin{}.conf".format(version_number))
                boot.boot(hostname, boot_file, config_file, struct_file)
                #used to hold up and wait for spinn board to have completed its boot up (only on rowleys board)
                time.sleep(1.0)
        else:
            raise exceptions.ExploreException("EXPLORE ERROR: Cannot ping"
                                              ,hostname,"- is it active on "
                                                        "the network?")

    def checkfile(self, test_file):
        real_file = test_file
        if not os.path.isfile(real_file):
            components = os.path.abspath(conf.__file__).split(os.sep)
            directory = os.path.abspath(os.path.join(os.sep,
                 *components[1:components.index("pacman103")]))
            real_file = os.path.join(directory,
                                     "spinnaker_tools",
                                     "boot", real_file)
            print real_file
        if not os.path.isfile(real_file):
            print "File %s not found" % test_file
            sys.exit(3)
        return real_file



    def select (self, *args):
        """
        Select the target node and processor.

        :param args: variadic argument (usage below)
        :raises:     ValueError

        This function has the following calling conventions:

            ``conn.select ('root')``
                Short-hand to select node (0, 0, 0)

            ``conn.select (N)``
                Selects processor N on the currently selected node

            ``conn.select (X, Y)``
                Selects processor 0 on node (``X``, ``Y``)

            ``conn.select (X, Y, N)``
                Selects processor ``N`` on node (``X``, ``Y``)

        """

        # extract the arguments
        if len (args) == 1 and type (args[0]) == str and args[0] == "root":
            (x, y, cpu) = (0, 0, 0)
        elif len (args) == 1 and type (args[0]) == int:
            (x, y, cpu) = (self._x, self._y, args[0])
        elif len (args) == 2:
            (x, y, cpu) = (args[0], args[1], 0)
        elif len (args) == 3:
            (x, y, cpu) = args
        else:
            raise ValueError ("invalid arguments given for SCPConnection."
                "select call.")

        # make sure that the variables are all ints
        if type (x) != int or type (y) != int or type (cpu) != int:
            raise ValueError ("invalid argument types given expecting ints or "
                "a single string 'root'.")

        # save the variables
        self.app_calls.set_view(x & 0xFF, y & 0xFF, cpu, (self._x << 8) | self._y)
        self.memory_calls.set_view(x & 0xFF, y & 0xFF, cpu, (self._x << 8) | self._y)
        self.packet_calls.set_view(x & 0xFF, y & 0xFF, cpu, (self._x << 8) | self._y)
        self.conn.set_view(x & 0xFF, y & 0xFF, cpu, (self._x << 8) | self._y)
        self._x = x & 0xFF
        self._y = y & 0xFF



