"""
The :py:mod:`pacman103.front.pynn` package contains the frontend specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN)

"""
import sys
import logging
import os
import math

from pacman103 import conf
from pacman103.core.utilities.timer import Timer
from pacman103.core.utilities import utility_calls

#from visualiser.visualiser import Visualiser
from visualiser import visualiser_modes
import inspect
import numpy

logger = logging.getLogger( __name__ )

from pacman103.core.dao import DAO
from pacman103.core import control
from pacman103.lib import graph, lib_map
from pacman103.core import exceptions
from pacman103.front.pynn.parameters_surrogate import PyNNParametersSurrogate

from pacman103.front.common.app_monitor import AppMonitor
from pacman103.front.common.projection_edge import ProjectionEdge
from pacman103.front.common.delay_projection_edge import DelayProjectionEdge
from pacman103.front.common.delay_afferent_edge import DelayAfferentEdge
from pacman103.front.common.delay_extension import DelayExtension
from pacman103.front.common.population_vertex import MAX_SUPPORTED_DELAY_TICS, PopulationVertex
from pacman103.front.common.delay_extension import MAX_DELAY_BLOCKS, MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

from synapse_dynamics import SynapseDynamics
from synapse_dynamics.stdp_mechanism import STDPMechanism
from synapse_dynamics.spike_pair_rule import SpikePairRule
from synapse_dynamics.spike_pair_rule_sinadd import SpikePairRuleSinAdd
from synapse_dynamics.additive_weight_dependence import AdditiveWeightDependence

from models import *
from connectors import *

from pyNN.random import *



controller = None
appMonitorVertex = None
multi_cast_vertex = None

def end():
    """
    Do any necessary cleaning up before exiting.

    Unregisters the controller
    """
    global controller
    controller.stop()
    controller = None


def num_processes():
    """
    Return the number of MPI processes (not used for SpiNNaker, always returns 1)
    """
    return 1

def rank():
    """
    Return the MPI rank of the current node. (not used for SpiNNaker, 
    always returns 0 - as this is the minimum rank suggesting the front node)
    """
    return 0


def reset():
    """
    Reset the time to zero, and start the clock.

    TO BE IMPLEMENTED
    """
    pass

def run(run_time = None, do_load = None, do_run = None):
    """
    Run the simulation for run_time ms.

    :param int run_time:
        simulation length (in ms)

    On run the following :py:class:`pacman103.core.control.Controller` functions are called:
     - :py:mod:`pacman103.core.control.Controller.map_model`
     - :py:mod:`pacman103.core.control.Controller.specify_output`
     - :py:mod:`pacman103.core.control.Controller.generate_output`
     - :py:mod:`pacman103.core.control.Controller.load_executables`
     - :py:mod:`pacman103.core.control.Controller.run`
    """
    global controller
    do_timing = conf.config.getboolean("Reports", "outputTimesForSections")

    if do_timing:
        timer = Timer()
    if do_load == None:
        do_load = True
        if conf.config.has_option("Execute", "load"):
            do_load = conf.config.getboolean("Execute", "load")
    
    if do_run == None:
        do_run = True
        if conf.config.has_option("Execute", "run"):
            do_run = conf.config.getboolean("Execute", "run")

    controller.dao.run_time = run_time
    logger.info("*** Running Mapper *** ")
    if do_timing:
        timer.start_timing()
    controller.map_model()
    if do_timing:
        timer.take_sample()

    if do_timing:
        timer.start_timing()
    logger.info("*** Generating Output *** ")
    logger.debug("")
    controller.generate_output()
    if do_timing:
        timer.take_sample()
    
    controller.start_visualiser()

    if do_timing:
        timer.start_timing()
    if(conf.config.getboolean("Execute", "run_simulation")):
        if do_load == True:
            logger.info("*** Loading data ***")
            controller.load_targets()
            controller.load_write_mem()
        if do_timing:
            timer.take_sample()
        
        if do_run == True:
            logger.info("*** Running simulation... *** ")
            controller.run(controller.dao.app_id)
    else:
        logger.info("*** No simulation requested: Stopping. ***")
    return run_time


def setup(timestep=None, min_delay=None, max_delay=None, **kwargs):
    """
    Should be called at the very beginning of a script.
    extra_params contains any keyword arguments that are required by a given
    simulator but not by others.
    For simulation on SpiNNaker the following parameters are mandatory:

    :param `pacman103.lib.lib_machine` machine:
        A SpiNNaker machine used to run the simulation.


    The setup() call instantiates a :py:class:`pacman103.core.control.Controller`
    object which is used as a global variable throughout the whole process.

    It also creates an AppMonitor Object (a vertex with model-type AppMon), 
    placing a mapping constraint on it so that it is on chip (0,0).
    This functionality may move elsewhere later.

    NB: timestep, min_delay and max_delay are required by the PyNN API but we
    ignore them because they have no bearing on the on-chip simulation code.
    """
    global controller

    logger.info("PACMAN103   (c) 2014 APT Group, University of Manchester")
    logger.info("                Release version 2014.4.1 - April 2014")
    # Raise an exception if no SpiNNaker machine is specified
    if kwargs.has_key("machine"):
        machine_name = kwargs.get("machine")
        logger.warn("The machine name from kwargs is overriding the machine "
                    "name defined in the pacman.cfg file")
    elif conf.config.has_option("Machine", "machineName"):
        machine_name = conf.config.get("Machine", "machineName")
    else:
        raise Exception("A SpiNNaker machine must be specified in pacman.cfg.")
    if machine_name == 'None':
        raise Exception("A SpiNNaker machine must be specified in pacman.cfg.")

    reload_time = None
    if conf.config.has_option("Execute", "reload_date"):
        reload_time = conf.config.get("Execute", "reload_date")
        if reload_time != 'None':
            logger.warn("The reload parameter was set, therefore not recompiling")
        else:
            reload_time = None

    #deal with params allowed via the setup optimals
    if timestep is not None:
        timestep *= 1000 # convert into ms from microseconds
        conf.config.set("Machine", "machineTimeStep", timestep)
    else:
        timestep = conf.config.get("Machine", "machineTimeStep")
    if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
        raise exceptions.ConfigurationException("Pacman does not support min "
                                                "delays below {} ms with the current "
                                                "machine time step".format(1.0 * timestep))

    natively_supported_delay_for_models = MAX_SUPPORTED_DELAY_TICS
    delay_extention_max_supported_delay = MAX_DELAY_BLOCKS * MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

    max_delay_tics_supported = \
        natively_supported_delay_for_models + delay_extention_max_supported_delay

    if max_delay is not None and float(max_delay * 1000) > max_delay_tics_supported * timestep:
        raise exceptions.ConfigurationException("Pacman does not support max delays "
                                                "above {} ms with the current machine "
                                                "time step".format(0.144 * timestep))
    if min_delay is not None:
        conf.config.add_section("Model")
        conf.config.set("Model", "min_delay", (min_delay * 1000) / timestep)

    if max_delay is not None:
        if not conf.config.has_section("Model"):
            conf.config.add_section("Model")
        conf.config.set("Model", "max_delay", (max_delay * 1000) / timestep)

    time_scale_factor = None
    if (conf.config.has_option("Machine", "timeScaleFactor") and
        conf.config.get("Machine", "timeScaleFactor") != "None"):
        time_scale_factor = conf.config.getint("Machine", "timeScaleFactor")
        if timestep * time_scale_factor < 1000:
            logger.warn("the combination of machine time step and the machine "
                        "time scale factor results in a real timer tic that is "
                        "currently not reliably supported by the spinnaker "
                        "machine.")
    else:
        time_scale_factor = max(1, math.ceil(1000.0 / float(timestep)))
        if time_scale_factor > 1:
            logger.warn("A timestep was entered that has forced pacman103 to "
                        "automatically slow the simulation down from real time "
                        "by a factor of {}. To remove this automatic behaviour"
                        ", please enter a timescaleFactor value in "
                        "your .pacman.cfg".format(time_scale_factor))




    
    # Create a new Controller to run PyNN:
    controller = control.Controller(sys.modules[__name__],
                                    machine_name, reload_time=reload_time)
    # Set the app ID:
    appID = conf.config.getint("Machine", "appID")
    controller.dao.app_id = appID
    logger.info("Setting appID to %d." % appID)
    # Set the machine time step for the simulation:
    machineTimeStep = conf.config.getint("Machine", "machineTimeStep")
    controller.dao.machineTimeStep = machineTimeStep
    logger.info("Setting machine time step to %d micro-seconds." % machineTimeStep)
    controller.dao.time_scale_factor = time_scale_factor
    logger.info("Setting time scale factor to %d." % time_scale_factor)
    # Set boolean variable writeTextSpecs in DAO if we are required to:
    writeTextSpecs = False
    if conf.config.getboolean("Reports", "reportsEnabled"):
        writeTextSpecs = conf.config.getboolean("Reports", "writeTextSpecs")
    controller.dao.writeTextSpecs = writeTextSpecs

    if conf.config.has_option("Recording", "send_live_spikes"):
        if conf.config.getboolean("Recording", "send_live_spikes") == True:
            port = None
            if conf.config.has_option("Recording", "live_spike_port"):
                port = conf.config.getint("Recording", "live_spike_port")
            hostname = "localhost"
            if conf.config.has_option("Recording", "live_spike_host"):
                hostname = conf.config.get("Recording", "live_spike_host")
            tag = None
            if conf.config.has_option("Recording", "live_spike_tag"):
                tag = conf.config.getint("Recording", "live_spike_tag")
            if tag == None:
                raise exceptions.PacmanException("Target tag for live spikes "
                                                 "has not been set")

            # Set up the forwarding so that monitored spikes are sent to the
            # requested location
            controller.set_tag_output(tag, port, hostname, 10)
            #takes the same port for the visualiser if being used
            if conf.config.getboolean("Visualiser", "enable") and \
               conf.config.getboolean("Visualiser", "have_board"):
                controller.set_visulaiser_port(port)
            
            # Create special AppMonitor vertex, to receive spikes for immediate 
            # transfer to host:
            monitorVertex = AppMonitor()
            
            # Add the special vertex to the list of vertices:
            controller.add_vertex(monitorVertex)
            
            # Get track of this special vertex as it will be used as a target
            # for recorded spikes:
            global appMonitorVertex
            appMonitorVertex = monitorVertex

    # PyNN API says something must be returned, 
    # so we return something useful: our controller instance
    return controller


def set_number_of_neurons_per_core(neuronType, maxPermitted):
    """
    Sets a ceiling on the number of neurons of a given type that can be placed
    on a single core.
    This information is stored in  dictionary in the dao and is referenced during
    the partition stage of the mapper.
    Note that each neuron type has a default value for this parameter that will 
    be used if no override is given.
    """
    if not inspect.isclass(neuronType):
        neuronType = globals()[neuronType]
        if neuronType is None:
            raise Exception("Unknown Vertex Type {}".format(neuronType))
        
    if hasattr(neuronType, "custom_max_atoms_per_core"):
        neuronType.custom_max_atoms_per_core = maxPermitted
    else:
        raise Exception("{} is not a Vertex type".format(neuronType))


class Projection(object):
    """
    A container for all the connections of a given type (same synapse type
    and plasticity mechanisms) between two populations, together with methods to
    set parameters of those connections, including of plasticity mechanisms.

    :param `pacman103.front.pynn.Population` presynaptic_population:
        presynaptic Population for the Projection
    :param `pacman103.front.pynn.Population` postsynaptic_population:
        postsynaptic Population for the Projection
    :param `pacman103.front.pynn.connectors` method:
        an instance of the connection method and parameters for the Projection
    """


    def __init__( self, presynaptic_population, postsynaptic_population,
        connector, source=None, target='excitatory', synapse_dynamics=None,
        label=None, rng=None):
        """
        Instantiates a :py:object:`Projection`.
        """
        global controller
        self.projection_edge = None
        if issubclass(type(postsynaptic_population.vertex), PopulationVertex):
            # Check that the "target" is an acceptable value
            targets = postsynaptic_population.vertex.get_synapse_targets()
            if not target in targets:
                raise exceptions.PacmanException("Target {} is not available in "
                        + "the post-synaptic population (choices are {})".format(
                                target, targets))
            synapse_type = postsynaptic_population.vertex.get_synapse_id(target)
        else:
            raise exceptions.ConfigurationException("postsynaptic_population is "
                                                    "not a supposal reciever of"
                                                    " synaptic projections")
        
        # Check that the edge doesn't already exist elsewhere
        # This would be a possible place for a merge at some point,
        # but this needs more thought
        for edge in controller.dao.get_edges():
            if (edge.prevertex == presynaptic_population.vertex and
                edge.postvertex == postsynaptic_population.vertex):
                    raise exceptions.PacmanException(
                            "More than one connection between the same pair of"
                            + " vertices is not currently supported")

        synapse_list = connector.generate_synapse_list(
                presynaptic_population.vertex, postsynaptic_population.vertex,
                1000.0 / controller.dao.machineTimeStep,
                synapse_type)
        self.read_synapse_list = None

        # If there are some negative weights
        if synapse_list.get_min_weight() < 0:
            
            # If there are mixed negative and positive weights, 
            # raise an exception
            if synapse_list.get_max_weight() > 0:
                raise exceptions.PacmanException("Weights must be positive")
            
            # Otherwise, the weights are all negative, so invert them(!)
            else:
                synapse_list.flip()
            
        # check if all delays requested can fit into the natively supported
        # delays in the models
        min_delay, max_delay = synapse_list.get_min_max_delay()
        natively_supported_delay_for_models = MAX_SUPPORTED_DELAY_TICS

        delay_extention_max_supported_delay = \
            MAX_DELAY_BLOCKS * MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        if max_delay > (natively_supported_delay_for_models 
                + delay_extention_max_supported_delay):
            raise exceptions.ConfigurationException("the max delay for projection {} is not "
                                                    "supported by the pacman "
                                                    "toolchain".format(max_delay))

        if conf.config.has_option("Model", "max_delay"):
            user_max_delay = conf.config.get("Model", "max_delay")
            if max_delay > user_max_delay:
                logger.warn("The end user entered a max delay to which the projection breaks")

        if (max_delay > natively_supported_delay_for_models):
            source_sz  = presynaptic_population.vertex.atoms
            self._addDelayExtension(source_sz, max_delay, natively_supported_delay_for_models,
                     connector, synapse_list, presynaptic_population,
                     postsynaptic_population, label, synapse_dynamics)

        else:
            self.projection_edge = ProjectionEdge(presynaptic_population.vertex,
                postsynaptic_population.vertex, controller.dao.machineTimeStep,
                synapse_list=synapse_list, synapse_dynamics=synapse_dynamics,
                label=label)
            self.delay_edge = None
            controller.add_edge(self.projection_edge)

    def _addDelayExtension(self, numSrcNeurons, max_delay_for_projection,
            max_delay_per_neuron, original_connector, original_synapse_list, 
            presynaptic_population, postsynaptic_population, label,
            synapse_dynamics):
        """
        Instantiate new delay extension component, connecting a new edge from 
        the source vertex to it and new edges from it to the target (given
        by numBlocks). 
        The outgoing edges cover each required block of delays, in groups of 
        MAX_DELAYS_PER_NEURON delay slots (currently 16).
        """
        global controller
        # If there are any connections with a delay of less than the maximum,
        # create a direct connection between the two populations only containing
        # these connections
        direct_synaptic_sublist = original_synapse_list.create_delay_sublist(
            0, max_delay_per_neuron)
        if (direct_synaptic_sublist.get_max_n_connections() != 0):
            direct_edge = ProjectionEdge(presynaptic_population.vertex,
                    postsynaptic_population.vertex, 
                    controller.dao.machineTimeStep,
                    synapse_list=direct_synaptic_sublist, label=label)
            controller.add_edge(direct_edge)
            self.projection_edge = direct_edge
        
        # Create a delay extension vertex to do the extra delays
        self.delay_vertex = presynaptic_population.vertex.delay_vertex
        if self.delay_vertex is None:
            sourceName = presynaptic_population.vertex.label
            delayName = "%s_delayed" % (sourceName)
            self.delay_vertex = DelayExtension(numSrcNeurons,
                max_delay_per_neuron, label = delayName)
            presynaptic_population.vertex.delay_vertex = self.delay_vertex
            #controller.add_vertex(self.delay_vertex)
        
        # Create a connection from the source population to the delay vertex
        new_label = "%s_to_DE" % (label)
        remaining_edge = DelayAfferentEdge(presynaptic_population.vertex,
                self.delay_vertex, label=new_label)
        controller.add_edge(remaining_edge)
        
        # Create a list of the connections with delay larger than that which 
        # can be handled by the neuron itself
        remaining_synaptic_sublist = original_synapse_list.create_delay_sublist(
                max_delay_per_neuron, max_delay_for_projection)
        
        
        # Create a special DelayEdge from the delay vertex to the outgoing
        # population, with the same set of connections
        delay_label = "DE to %s" % (label)
        num_blocks = int(math.ceil(float(max_delay_for_projection)
                                 / float(max_delay_per_neuron))) - 1
        self.delay_edge = DelayProjectionEdge(self.delay_vertex, 
                postsynaptic_population.vertex, controller.dao.machineTimeStep,
                num_blocks, max_delay_per_neuron,
                synapse_list = remaining_synaptic_sublist,
                synapse_dynamics=synapse_dynamics, label=delay_label)
        controller.add_edge(self.delay_edge)

    def describe(self, template='projection_default.txt', engine='default'):
        """
        Returns a human-readable description of the projection.

        The output may be customized by specifying a different template
        togther with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the `i`th connection within the Projection."""
        raise NotImplementedError
    
    def _get_synaptic_data(self):
        if self.read_synapse_list is None:
        
            global controller
            synapse_list = None
            delay_synapse_list = None
            if self.projection_edge is not None:
                synapse_list = self.projection_edge.get_synaptic_data(
                        controller, MAX_SUPPORTED_DELAY_TICS)
            if self.delay_edge is not None:
                delay_synapse_list = self.delay_edge.get_synaptic_data(
                        controller, MAX_SUPPORTED_DELAY_TICS)
            
            # If there is both a delay and a non-delay list, merge them
            if synapse_list is not None and delay_synapse_list is not None:
                rows = synapse_list.get_rows()
                delay_rows = delay_synapse_list.get_rows()
                for i in range(len(rows)):
                    rows[i].append(delay_rows[i])
                self.read_synapse_list = synapse_list
            
            # If there is only a synapse list, return that
            elif synapse_list is not None:
                self.read_synapse_list = synapse_list
            
            # Otherwise return the delay list (there should be at least one!)
            else:
                self.read_synapse_list = delay_synapse_list
        
        return self.read_synapse_list

    def getDelays(self, format='list', gather=True):
        """
        Get synaptic delays for all connections in this Projection.

        Possible formats are: a list of length equal to the number of connections
        in the projection, a 2D delay array (with NaN for non-existent
        connections).
        """
        global controller
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        synapse_list = self._get_synaptic_data()
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
            
        if format == 'list':
            delays = list()
            for row in synapse_list.get_rows():
                delays.extend(row.delays 
                        * (float(controller.dao.machineTimeStep) / 1000.0))
            return delays
        
        delays = numpy.zeros((self.projection_edge.prevertex.atoms, 
                self.projection_edge.postvertex.atoms))
        rows = synapse_list.get_rows()
        for pre_atom in range(len(rows)):
            row = rows[pre_atom]
            for i in len(row.target_indices):
                post_atom = row.target_indices[i]
                delay = (float(row.delays[i]) 
                        * (float(controller.dao.machineTimeStep) / 1000.0))
                delays[pre_atom][post_atom] = delay
        return delays

    def getSynapseDynamics(self, parameter_name, format='list', gather=True):
        """
        Get parameters of the dynamic synapses for all connections in this
        Projection.
        """
        raise NotImplementedError

    def getWeights(self, format='list'):
        """
        Get synaptic weights for all connections in this Projection.
        (pyNN gather parameter not supported from the signiture
        getWeights(self, format='list', gather=True):)

        Possible formats are: a list of length equal to the number of connections
        in the projection, a 2D weight array (with NaN for non-existent
        connections). Note that for the array format, if there is more than
        one connection between two cells, the summed weight will be given.
        """
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        synapse_list = self._get_synaptic_data()
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
            
        if format == 'list':
            weights = list()
            for row in synapse_list.get_rows():
                weights.extend(row.weights)
            return weights 
        elif format == 'array':
            weights = numpy.zeros((self.projection_edge.prevertex.atoms, 
                                   self.projection_edge.postvertex.atoms))
            rows = synapse_list.get_rows()
        for pre_atom, row in enumerate(rows):
            for post_atom, weight in zip(row.target_indices, row.weights):
                weights[pre_atom][post_atom] = weight
        return weights

    def __len__(self):
        """Return the total number of local connections."""
        raise NotImplementedError

    def printDelays(self, file, format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        raise NotImplementedError

    def printWeights(self, file, format='list', gather=True):
        """
        Print synaptic weights to file. In the array format, zeros are printed
        for non-existent connections.
        """
        raise NotImplementedError

    def randomizeWeights(self, rand_distr):
        """
        Set weights to random values taken from rand_distr.
        """
        raise NotImplementedError

    def randomizeDelays(self, rand_distr):
        """
        Set delays to random values taken from rand_distr.
        """
        raise NotImplementedError

    def randomizeSynapseDynamics(self, param, rand_distr):
        """
        Set parameters of the synapse dynamics to values taken from rand_distr
        """
        raise NotImplementedError

    def __repr__(self):
        '''
        returns a string rep of the projection
        '''
        return "prjection {}".format(self.projection_edge.label)

    def saveConnections(self, file, gather=True, compatible_output=True):
        """
        Save connections to file in a format suitable for reading in with a
        FromFileConnector.
        """
        raise NotImplementedError

    def size(self, gather=True):
        """
        Return the total number of connections.
         - only local connections, if gather is False,
         - all connections, if gather is True (default)
        """
        raise NotImplementedError

    def setDelays(self, d):
        """
        d can be a single number, in which case all delays are set to this
        value, or a list/1D array of length equal to the number of connections
        in the projection, or a 2D array with the same dimensions as the
        connectivity matrix (as returned by `getDelays(format='array')`).
        """
        raise NotImplementedError

    def setSynapseDynamics(self, param, value):
        """
        Set parameters of the dynamic synapses for all connections in this
        projection.
        """
        raise NotImplementedError

    def setWeights(self, w):
        """
        w can be a single number, in which case all weights are set to this
        value, or a list/1D array of length equal to the number of connections
        in the projection, or a 2D array with the same dimensions as the
        connectivity matrix (as returned by `getWeights(format='array')`).
        Weights should be in nA for current-based and uS for conductance-based
        synapses.
        """
        raise NotImplementedError

    def weightHistogram(self, min=None, max=None, nbins=10):
        """
        Return a histogram of synaptic weights.
        If min and max are not given, the minimum and maximum weights are
        calculated automatically.
        """
        raise NotImplementedError





class Population( object ):
    """
    A collection neuron of the same types. It encapsulates a type of :class:`pacman103.lib.graph.Vertex`
    used with Spiking Neural Networks, comprising n cells (atoms)
    of the same :py:mod:`pacman103.front.pynn.models` type.

    :param int size:
        size (number of cells) of the Population.
    :param `pacman103.front.pynn.models` cellclass:
        specifies the neural model to use for the Population
    :param dict cellparams:
        a dictionary containing model specific parameters and values
    :param `pyNN.space` structure:
        a spatial structure - not supported
    :param string label:
        a label identifying the Population


    """

    def __init__(self, size, cellclass, cellparams, structure=None, label=None):
        """
        Instantiates a :py:object:`Population`.
        """
        global controller, multi_cast_vertex

        # Raise an exception if the Pop. attempts to employ spatial structure
        if structure:
            raise Exception("Spatial structure is unsupported for Populations.")

        # Create a graph vertex for the population and add it to PACMAN
        self.vertex = cellclass(size, label=label, **cellparams)

        #check if the vertex is a cmd sender, if so store for future
        if self.vertex.requires_multi_cast_source():
            if multi_cast_vertex is None:
                multi_cast_vertex = MultiCastSource()
                controller.add_vertex(multi_cast_vertex)
            edge = graph.Edge(multi_cast_vertex, self.vertex)
            controller.add_edge(edge)

        self.parameters = PyNNParametersSurrogate(self.vertex)
        controller.add_vertex(self.vertex)

        #add any dependant edges and verts if needed
        dependant_verts, dependant_edges = \
            self.vertex.get_dependant_vertexes_edges()

        if dependant_verts is not None:
            for dependant_vert in dependant_verts:
                controller.add_vertex(dependant_vert)

        if dependant_edges is not None:
            for dependant_edge in dependant_edges:
                controller.add_edge(dependant_edge)

        #initlise common stuff
        self.size = size
        self.recordSpikeFile = None
        self.recordVFile = None
        self.recordGSynFile = None

    def __add__(self, other):
        '''
        merges populations
        '''
        raise NotImplementedError

    def _add_recorder(self, variable):
        """Create a new Recorder for the supplied variable."""
        raise NotImplementedError

    def all(self):
        '''
        Iterator over cell ids on all nodes.
        '''
        raise NotImplementedError

    @property
    def conductance_based(self):
        '''
        returns a boolean based on if the population is a conductance based pop
        '''
        raise NotImplementedError

    def describe(self, template='population_default.txt', engine='default'):
        """
        Returns a human-readable description of the population.

        The output may be customized by specifying a different template
        togther with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        raise NotImplementedError

    @property
    def grandparent(self):
        raise NotImplementedError

    def get(self, paramter_name, gather=False):
        '''
        Get the values of a parameter for every local cell in the population.
        '''
        raise NotImplementedError

    def _get_cell_position(self, id):
        '''
        returns the position of a cell (no idea what a cell is)
        '''
        raise NotImplementedError

    def _get_cell_initial_value(self, id, variable):
        '''
        set a given cells intial value
        '''
        raise NotImplementedError


    def getSpikes(self, compatible_output=False, gather=True):
        """
        Return a 2-column numpy array containing cell ids and spike times for
        recorded cells.   This is read directly from the memory for the board.
        """
        global controller
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        spikes = self.vertex.getSpikes(controller, controller.dao.run_time, compatible_output)

        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
        return spikes

    def get_spike_counts(self, gather=True):
        """
        Returns the number of spikes for each neuron.
        """
        raise NotImplementedError


    def get_gsyn(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic conductances for recorded cells.

        """
        global controller
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        gsyn = self.vertex.get_gsyn(controller, gather=gather, compatible_output=compatible_output)
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
        return gsyn

    def get_v(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        global controller
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        v = self.vertex.get_v(controller, gather=gather, compatible_output=compatible_output)

        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()

        return v

    def id_to_index(self, id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population).
        """
        raise NotImplementedError

    def id_to_local_index(self, id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population), counting only cells on the local MPI node.
        """
        raise NotImplementedError

    def initialize(self, variable, value):
        """
        Set the initial value of one of the state variables of the neurons in this population.

        """
        initialize_attr = getattr(self.vertex, "initialize_%s" % variable, None)
        if ((initialize_attr == None) or not callable(initialize_attr)):
            raise Exception("Vertex does not support initialization of parameter %s" % variable)

        initialize_attr(value)

    def is_local(self, id):
        '''
        Determine whether the cell with the given ID exists on the local MPI node.
        '''
        raise NotImplementedError

    def can_record(self, variable):
        """Determine whether `variable` can be recorded from this population."""
        raise NotImplementedError

    def inject(self, current_source):
        """
        Connect a current source to all cells in the Population.
        """
        raise NotImplementedError

    def __iter__(self):
        '''
        suppose to iterate over local cells
        '''
        raise NotImplementedError

    def __len__(self):
        """
        Returns the total number of cells in the population.
        """
        return self.size

    @property
    def local_size(self):
        '''
        returns the number of local cells ???
        '''
        raise NotImplementedError

    def meanSpikeCount(self, gather=True):
        """
        Returns the mean number of spikes per neuron.
        """
        raise NotImplementedError

    def nearest(self, position):
        '''
        return the neuron closest to the specificed position
        '''
        raise NotImplementedError

    @property
    def position_generator(self):
        '''
        returns a position generator
        '''
        raise NotImplementedError

    def randomInit(self, distribution):
        """
        Set initial membrane potentials for all the cells in the population to random values.

        :param `pyNN.random.RandomDistribution` distribution:
            the distribution used to draw random values.

        """
        newEntryForVInit = {'v_init': distribution}
        self.parameters.update(newEntryForVInit)

    def stream(self):
        # If the monitor is enabled, add an edge to the monitor
        global appMonitorVertex
        self.vertex.setup_visualizer(visualiser_mode=visualiser_modes.RASTER)
        if appMonitorVertex != None:
            controller.add_edge(graph.Edge(self.vertex, appMonitorVertex))
            
    def record(self, to_file=None,
               focus=None, visualiser_mode=visualiser_modes.RASTER,
               visualiser_2d_dimension=None, visualiser_raster_seperate=None,
               visualiser_no_colours=None, visualiser_average_period_tics=None,
               visualiser_longer_period_tics=None,
               visualiser_update_screen_in_tics=None,
               visualiser_reset_counters=None,
               visualiser_reset_counter_period=None, 
               stream=True):
        """
        Record spikes from all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering spike time recording.
        """
        record_attr = getattr(self.vertex, "record", None)
        if ((record_attr == None) or not callable(record_attr)):
            raise Exception("Vertex does not support recording of spikes")


        # Tell the vertex to record spikes
        self.vertex.record()
        self.recordSpikeFile = to_file
        
        if stream:
            self.vertex.setup_visualizer(focus=focus, visualiser_mode=visualiser_mode,
                           visualiser_2d_dimension=visualiser_2d_dimension,
                           visualiser_raster_seperate=visualiser_raster_seperate,
                           visualiser_no_colours=visualiser_no_colours,
                           visualiser_average_period_tics=visualiser_average_period_tics,
                           visualiser_longer_period_tics=visualiser_longer_period_tics,
                           visualiser_update_screen_in_tics=visualiser_update_screen_in_tics,
                           visualiser_reset_counters=visualiser_reset_counters,
                           visualiser_reset_counter_period=visualiser_reset_counter_period)

            # If the monitor is enabled, add an edge to the monitor
            global appMonitorVertex
            if appMonitorVertex != None:
                controller.add_edge(graph.Edge(self.vertex, appMonitorVertex))

    def record_gsyn(self, to_file=None):
        """
        Record the synaptic conductance for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering gsyn value recording.
        """
        if (not hasattr(self.vertex, "record_gsyn")
                or not callable(self.vertex.record_gsyn)):
            raise Exception("Vertex does not support recording of gsyn")

        self.vertex.record_gsyn()
        self.recordGSynFile = to_file

    def record_v(self, to_file=None):
        """
        Record the membrane potential for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering potential recording.
        """
        if (not hasattr(self.vertex, "record_v")
                or not callable(self.vertex.record_v)):
            raise Exception("Vertex does not support recording of potential")

        self.vertex.record_v()
        self.recordVFile = to_file

    @property
    def positions(self):
        raise NotImplementedError

    def printSpikes(self, filename, gather=True):
        """
        Write spike time information from the population to a given file.
        """
        spikes = self.getSpikes(compatible_output=True)
        if spikes != None:
            first_id = 0
            num_neurons = self.vertex.atoms
            dimensions = self.vertex.atoms
            last_id = self.vertex.atoms - 1
            utility_calls.check_directory_exists(filename)
            spikeFile = open(filename, "w")
            spikeFile.write("# first_id = %d\n" % first_id)
            spikeFile.write("# n = %d\n" % num_neurons)
            spikeFile.write("# dimensions = [%d]\n" % dimensions)
            spikeFile.write("# last_id = %d\n" % last_id)
            for (neuronId, time) in spikes:
                spikeFile.write("%d\t%d\n" % (time, neuronId))
            spikeFile.close()

    def print_gsyn(self, filename, gather=True):
        """
        Write conductance information from the population to a given file.

        """
        global controller
        timeStep = (controller.dao.machineTimeStep*1.0)/1000.0
        gsyn = self.get_gsyn(gather, compatible_output=True)
        first_id = 0
        num_neurons = self.vertex.atoms
        dimensions = self.vertex.atoms
        fileHandle = open(filename, "w")
        fileHandle.write("# first_id = %d\n" % first_id)
        fileHandle.write("# n = %d\n" % num_neurons)
        fileHandle.write("# dt = %f\n" % timeStep)
        fileHandle.write("# dimensions = [%d]\n" % dimensions)
        fileHandle.write("# last_id = %d\n" % num_neurons-1)
        utility_calls.check_directory_exists(filename)
        fileHandle = open(filename, "w")
        for (neuronId, time, value) in gsyn:
            fileHandle.write("%f\t%d\t%f\n" % (time, neuronId, value))
        fileHandle.close()

    def print_v(self, filename, gather=True):
        """
        Write membrane potential information from the population to a given file.

        """
        global controller
        timeStep = (controller.dao.machineTimeStep*1.0)/1000.0
        v = self.get_v(gather, compatible_output=True)
        utility_calls.check_directory_exists(filename)
        fileHandle = open(filename, "w")
        first_id = 0
        num_neurons = self.vertex.atoms
        dimensions = self.vertex.atoms
        fileHandle.write("# first_id = %d\n" % first_id)
        fileHandle.write("# n = %d\n" % num_neurons)
        fileHandle.write("# dt = %f\n" % timeStep)
        fileHandle.write("# dimensions = [%d]\n" % dimensions)
        fileHandle.write("# last_id = %d\n" % (num_neurons-1))
        for (neuronId, time, value) in v:
            fileHandle.write("%f\t%d\n" % (value, neuronId))
        fileHandle.close()

    def rset(self, parametername, rand_distr):
        """
        'Random' set. Set the value of parametername to a value taken from
        rand_distr, which should be a RandomDistribution object.
        """
        raise NotImplementedError

    def sample(self, n, rng=None):
        '''
        returns a random selection fo neurons from a population in the form
        of a population view
        '''
        raise NotImplementedError

    def save_positions(self, file):
        '''
        save positions to file
        '''
        raise NotImplementedError


    def set(self, *args, **kargs):
        """
        converts key value pairs in key args into a collection of string
        parameter and value entries used with old fashion set.

        Assumes parameters_surrogate will throw error when entries not
        avilable for a vertex is given
        """
        if len(args) == 0:
            for key in kargs.keys():
                self._set_string_value_pair(key, kargs[key])
        else:
            for element in range(0, len(args), 2):
                self._set_string_value_pair(args[element], args[element+1])

    def _set_cell_initial_value(self, id, variable, value):
        '''
        set a given cells intial value
        '''
        raise NotImplementedError

    def _set_cell_position(self, id, pos):
        '''
        sets a cell to a given position
        '''
        raise NotImplementedError

    def _set_string_value_pair(self, parameter, value=None):
        """
        Set one or more parameters for every cell in the population.

        param can be a dict, in which case val should not be supplied, or a string
        giving the parameter name, in which case val is the parameter value.
        val can be a numeric value, or list of such (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})
        """
        if type(parameter) is str:
            if value==None:
                raise Exception("Error: No value given in set() function for population parameter. Exiting.")
            self.parameters[parameter] = value
            return
        if type(parameter) is not dict:
                raise Exception("Error: invalid parameter type for set() function for population parameter. Exiting.")
        # Add a dictionary-structured set of new parameters to the current set:
        self.parameters.update(parameter)

    def set_mapping_constraint(self, constraint):
        """
        Apply a constraint to a population that restricts the processor
        onto which its sub-populations will be placed.
        """
        placementConstraint = lib_map.VertexConstraints()
        if 'x' in constraint:
            placementConstraint.x = constraint['x']
        if 'y' in constraint:
            placementConstraint.y = constraint['y']
        if 'p' in constraint:
            placementConstraint.p = constraint['p']
        self.vertex.constraints = placementConstraint

    @property
    def structure(self):
        raise NotImplementedError

    def tset(self, parametername, value_array):
        """
        'Topographic' set. Set the value of parametername to the values in
        value_array, which must have the same dimensions as the Population.
        """
        raise NotImplementedError


