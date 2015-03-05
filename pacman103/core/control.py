import logging

from pacman103.core.spinnman.interfaces.transceiver import Transceiver
from pacman103.core.spinnman.interfaces.tubotron import Tubotron
from pacman103.core.spinnman.interfaces.iptag import IPTag

from pacman103.core import dao, output_generator, reports
from pacman103.core.mapper import partitioner_algorithms, \
    placer_algorithms, key_allocator_algorithms, routing_algorithms
from pacman103.core.mapper.router.router import Router

from pacman103 import conf
from pacman103.core.process_bar import ProgressBar

if conf.config.getboolean("Visualiser", "enable"):
    from visualiser.visualiser import Visualiser

logger = logging.getLogger(__name__)


class Controller(object):
    """
    A Controller is instantiated by a front-end in order to map a model to
    SpiNNaker, load it to the machine, run it and retrieve the results.
    The Controller provides functions for the front-end to trigger each of
    these stages and instantiates a :py:class:`pacman103.core.dao.DAO` object
    in which front-end inputs and results of the mapping processes are stored
    and a :py:class:`pacman103.core.transceiver.Transceiver` through which
    simulations are loaded to SpiNNaker and observed.

    :param module front_end:
        front-end package
    :param string hostname:
        hostname of the SpiNNaker machine on which the simulation is to be run.
    :param dict kwargs:
        key word arguments, of which there are currently none.
    """

    partitioner_algorithms_list = conf.get_valid_components(
        partitioner_algorithms, "Partitioner"
    )

    placer_algorithms_list = conf.get_valid_components(
        placer_algorithms, "Placer"
    )

    key_allocator_algorithms_list = conf.get_valid_components(
        key_allocator_algorithms, "KeyAllocator"
    )

    routing_algorithms_list = conf.get_valid_components(
        routing_algorithms, "Routing"
    )

    utility = None

    def __init__(self, front_end, hostname, reload_time=None, **kwargs):
        self.hostname = hostname
        self.dao = dao.DAO(front_end)
        self.reload_time = reload_time

        self.txrx = None
        self.app_id = None
        self.tubotron = None
        self.leaveTubotronRunning = False
        self.visualiser = None
        self.wait_for_run = False
        self.visualiser_port = None

        #setting tuborotron to false, so that in theory our strange tubotron doesnt operate
        conf.config.set("Tubotron", "enable", "False")


    #ABS changed so that iptag is sotred into dao instead of
    # transmitting immediately
    def set_tag_output(self, tag, port, hostname="localhost", timeout=10):
        self.dao.add_iptag(IPTag(tag=tag, port=port,
                                 hostname=hostname, timeout=timeout))

    def add_vertex(self, vertex):
        """
        Adds a vertex object to the datastore. This is simply a convenience
        function that wraps :py:func:`pacman103.core.dao.DAO.add_vertex` to
        save the front-end from directly interacting with the datastore.

        :param `pacman103.lib.graph.Vertex` vertex:
            Vertex object to be added.
        """
        return self.dao.add_vertex(vertex)

    def get_multi_cast_vertex(self):
        return self.dao.multi_cast_vertex

    def add_edge(self, edge):
        """
        Adds an edge object to the datastore. This is simply a convenience
        function that wraps :py:func:`pacman103.core.dao.DAO.add_edge` to save
        the front-end from directly interacting with the datastore.

        :param `pacman103.lib.graph.Edge` edge:
            Edge object to be added.
        """
        self.dao.add_edge(edge)

    def add_rng(self, rngIndex, rngInfo):
        """Adds a random number generator object to the datastore. This is
        simply a convenience function that wraps
        :py:func:`pacman103.core.dao.DAO.add_rng` to save the front-end from
        directly interacting with the datastore.
        """
        logger.debug("Controller adding RNG")
        self.dao.add_rng(rngIndex, rngInfo)

    def add_random_distribution(self, distIndex, distInfo):
        """
        Adds a random distribution object to the datastore. This is simply a
        convenience function that wraps
        :py:func:`pacman103.core.dao.DAO.add_randomDistribution` to save the
        front-end from directly interacting with the datastore.
        """
        logger.debug("Controller adding random dist")
        self.dao.add_randomDistribution(distIndex, distInfo)

    def generate_output(self):
        """
        Generates simulation data structures and prepares load targets and
        execution targets.
        """
        if self.reload_time is None:
            output_generator.generate_output(self.dao)
        else:
            output_generator.reload_output(self.dao, self.reload_time)

    def load_write_mem(self):
        """
        Loads the simulation memory writes to the board via the transceiver.
        """
        self.txrx.load_write_mem(self.dao)

    def load_targets(self):
        """
        Loads the simulation executables and data structures to the board via
        the transceiver.
        """
        self.txrx.load_targets(self.dao)

    def map_model(self):
        """Map an input graph to a SpiNNaker machine via the partitioning,
        placement and routing stages. See :py:mod:`pacman103.core.mapper` for
        more details.

        *Side effects*:
            populates the datastore with information proceeding from each stage
            of mapping.
        """
        self.setup_spinnman_interfaces()

        report_dir = self.dao.get_reports_directory()
        enabledReports = False
        if (conf.config.getboolean("Reports", "reportsEnabled")):
            enabledReports = True
        if enabledReports:
            reports.generate_network_report(self.dao)
            reports.generate_machine_report(self.dao)
        #check if each flag has been set before running a method
        #partitioning verts into subverts
        if not self.dao.done_partitioner:
            self.execute_partitioning()

        # placing subverts onto machine structure
        # (can be done by preivous systems if merged)
        if not self.dao.done_placer:
            self.execute_placer()
        if enabledReports:
            reports.generate_placement_reports(self.dao)

        #allocate keys to subedges so that its done up front
        # (no report, as covered by the router report)
        if not self.dao.done_key_allocation:
            self.execute_key_alloc()

        #route packets from subverts through subedges
        if not self.dao.done_router:
            self.filterSubEdges(self.dao)
            self.execute_routing()
        if enabledReports:
            reports.generate_routing_report(self.dao)

        #if not self.dao.done_inverse_mapper:
        #    InverseMapper.build_inverse_map(self.dao)
        if enabledReports:
            reports.generate_coremap_report(self.dao)

    def execute_partitioning(self):
        """Handle the execution of a partitioning algorithm
        """
        try:
            partitioner_class = Controller.partitioner_algorithms_list[
                conf.config.get("Partitioner", "algorithm")]
            partitioner = partitioner_class(self.dao)
            partitioner.partition()
        except KeyError as e:
            raise ValueError("Invalid partitioner algorithm specified. "
                             " I don't know '%s'." % e)

    def execute_placer(self):
        """Handle the exeuction of a placer algorithm
        """
        try:
            placer_class = Controller.placer_algorithms_list[
                conf.config.get("Placer", "algorithm")
            ]
            placer = placer_class(self.dao)
            placer.place_all()
        except KeyError as e:
            raise ValueError("Invalid partitioner algorithm specified. "
                             " I don't know '%s'." % e)

    def execute_key_alloc(self):
        """Handle the execution of a key allocator
        """
        try:
            key_allocator_class = Controller.key_allocator_algorithms_list[
                conf.config.get("Key_allocator", "algorithm")]
            key_allocer = key_allocator_class(self.dao)
            key_allocer.allocate_keys()
        except KeyError as e:
            raise ValueError("Invalid key alloc algorithm specified. "
                             " I don't know '%s'." %
                             conf.config.get("Key_allocator", "algorithm")
                             )

    def execute_routing(self):
        """Execute routing
        """
        try:
            router = Router(self.dao)
            router.route()
        except KeyError as e:
            raise ValueError("Invalid partitioner algorithm specified. "
                             " I don't know '%s'." % e)

    def start_visualiser(self):
        """Start the Visualiser thread
        """
        if (conf.config.getboolean("Visualiser", "enable") and not
                conf.config.getboolean("Visualiser", "have_board")):
                self.visualiser.start()

    def set_visulaiser_port(self, port):
        """Set the port that the Visualiser listens to for packets
        """
        self.visualiser_port = port

    def setup_spinnman_interfaces(self):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        self.dao.set_hostname(self.hostname)
        self.txrx = Transceiver(self.hostname)

        # Start local tubotron if requested
        if conf.config.getboolean("Visualiser", "enable"):
            self.wait_for_run = conf.config.getboolean(
                "Visualiser", "pause_before_run"
            )
            if self.wait_for_run:
                self.visualiser = Visualiser(
                    self.dao, start_simulation_method=getattr(self, "run_now")
                )
            else:
                self.visualiser = Visualiser(self.dao)
            self.visualiser.set_port(self.visualiser_port)

        tubotron_port = conf.config.getint("Tubotron", "port")
        tubotron_tag = conf.config.getint("Tubotron", "tag")
        tubotron_host = conf.config.get("Tubotron", "hostname")

        self.set_tag_output(tubotron_tag, tubotron_port, tubotron_host)

        if conf.config.getboolean("Tubotron", "enable"):
            if tubotron_host == "localhost":
                self.tubotron = Tubotron(tubotron_port)
            if conf.config.has_option("Tubotron", "leaveRunning"):
                self.leaveTubotronRunning = conf.config.getboolean(
                    "Tubotron", "leaveRunning")

    def run(self, app_id):
        """Trigger execution of the simulation on SpiNNaker via the
        transceiver.
        """
        self.app_id = app_id
        if (conf.config.getboolean("Visualiser", "enable") and
                conf.config.getboolean("Visualiser", "have_board")):
            self.visualiser.start()
        if not self.wait_for_run:
            self.run_now()
        else:
            print "Waiting for run command..."
            self.visualiser.wait_for_finish()

    def run_now(self):
        """Start a already loaded application
        """
        if self.tubotron is not None:
            self.tubotron.start()
            if (self.dao.run_time is not None and self.dao.run_time > 0 
                   and not self.leaveTubotronRunning):
                self.tubotron.set_timeout((self.dao.run_time / 1000.0) + 1)
        self.txrx.run(self.dao, self.app_id)

    def stop(self):
        """Stop a running application
        """
        if self.tubotron is not None:
            self.tubotron.stop()

    def filterSubEdges(self, dao):
        """Go through the newly created list of sub-edges and call a model
        specific function on each one, this allows the application to prune
        sub-edges that are not really needed.
        """
        logger.info("* Running pre-routing sub-edge pruning *")
        new_subedges = list()
        progress = ProgressBar(len(dao.subedges))
        for subedge in dao.subedges:
            if subedge.edge.filterSubEdge(subedge):
                subedge.pruneable = True
            else:
                new_subedges.append(subedge)
            progress.update()
        dao.subedges = new_subedges
        
        progress.end()
