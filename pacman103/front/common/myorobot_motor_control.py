__author__ = 'stokesa6'
from pacman103.front.common.population_vertex import PopulationVertex
from pacman103.front.common.external_motor_device import ExternalMotorDevice
from pacman103.front.common.spike_source_remote import SpikeSourceRemote
from pacman103.lib import data_spec_constants, data_spec_gen, lib_map
from pacman103.lib.graph.edge import Edge
from pacman103.core.utilities import packet_conversions
from pacman103.core import exceptions
from itertools import count # for counting our instances
import os

INFINITE_SIMULATION = 4294967295

class MyoRobotMotorControl(PopulationVertex):

    SYSTEM_REGION = 1
    PARAMS = 2
    SYSTEM_SIZE = 16
    PARAMS_SIZE = 8 * 4

    core_app_identifier = \
        data_spec_constants.EXTERNAL_RETINA_SETUP_DEVICE_CORE_APPLICATION_ID

    _myocount = count(0)
    
    '''
    constructor that depends upon the Component vertex
    '''
    def __init__(self, n_neurons, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge, output_scale = 10.0, sample_time = 100,
                 decay_factor = 0.2, kernel_amplitude = 1.0, threshold = 16,
                 motorID = 0x110, monitorID = 0x120, enableSensors = 0xf,
                 label="MyoRobotMotorControl"):
        super(MyoRobotMotorControl, self).__init__(n_neurons = n_neurons, n_params = 3,
            binary = "myorobot_motor_control.aplx", label=label)

        self.n_neurons = n_neurons
        self.virtual_chip_coords = virtual_chip_coords
        self.connected_chip_coords = connected_chip_coords
        self.connected_chip_edge = connected_chip_edge
        self.out_going_edge = None

        self.output_scale = output_scale
        self.sample_time = sample_time
        self.decay_factor = decay_factor    # TODO: compute considering timestep
        self.kernel_amplitude = kernel_amplitude
        self.threshold = threshold
        
        self.myoID = self._myocount.next()
        self.motorCANID = motorID
        self.monitorCANID = monitorID
        self.enableSensors = enableSensors
    
    def get_synapse_targets(self):
        """
        Gets the supported names of the synapse targets
        """
        return ("excitatory", "excitatory2", "inhibitory") # TODO: we don't really have these!
    
    def get_synapse_id(self, target_name):
        """
        Returns the numeric identifier of a synapse, given its name.  This
        is used by the neuron models.
        """
        if target_name == "excitatory": #TODO clean away!
            return 0
        elif target_name == "excitatory2":
            return 1
        elif target_name == "inhibitory":
            return 2
        return None
    
    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 2
    

    def get_dependant_vertexes_edges(self):
        ext = ExternalMotorDevice(1, self.virtual_chip_coords,
                                self.connected_chip_coords,
                                self.connected_chip_edge)
        virtual_vertexes=[ext] 
            
        self.out_going_edge = Edge(self, ext)
#        virtual_edges = [Edge(self,v) for v in virtual_vertexes]
        virtual_edges = [Edge(self,ext)]
        return virtual_vertexes, virtual_edges


    """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
    """
    def generateDataSpec(self, processor, subvertex, dao):

        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor=processor, dao=dao)
        spec.initialise(self.core_app_identifier, dao) # User specified identifier

        spec.comment("\n*** Spec for robot motor control ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        populationIdentity = packet_conversions.get_key_from_coords(x, y, p+1) #our own key
            
        file_path = os.path.join(dao.get_common_binaries_directory(),
                                 'myorobot_motor_control.aplx')
        executable_target = lib_map.ExecutableTarget(file_path, x, y, p)
        memory_write_targets = list()

        simulationTimeInTicks = INFINITE_SIMULATION
        if dao.run_time is not None:
            simulationTimeInTicks = int((dao.run_time * 1000.0) 
                    /  dao.machineTimeStep)
        user1Addr = 0xe5007000 + 128 * p + 116 # User1 location reserved for core p
        memory_write_targets.append(lib_map.MemWriteTarget(x, y, p, user1Addr,
                                                           simulationTimeInTicks))

        #reserve regions
        self.reserve_memory_regions(spec)
        
        #write system info
        spec.switchWriteFocus(region = self.SYSTEM_REGION)
        spec.write(data = 0xBEEF0000)
        spec.write(data = 0)
        spec.write(data = 0)
        spec.write(data = 0)
        edge_key = None
        #locate correct subedge for key
        for subedge in subvertex.out_subedges:
            if subedge.edge == self.out_going_edge:
                edge_key = subedge.key

        #write params to memory

        spec.switchWriteFocus(region=self.PARAMS)
        spec.write(data=edge_key|self.myoID)
#        spec.write(data=populationIdentity)
        spec.write(data=spec.doubleToS1615(self.output_scale),sizeof='s1615')
        spec.write(data=self.sample_time)
        spec.write(data=spec.doubleToS1615(self.decay_factor), sizeof='s1615')
        spec.write(data=spec.doubleToS1615(self.kernel_amplitude), sizeof='s1615')
        spec.write(data=self.threshold)
        spec.write(data=self.n_neurons)

        # End-of-Spec:
        spec.endSpec()
        spec.closeSpecFile()
        load_targets = list()

        # Return list of executables, load files:
        return executable_target, load_targets, memory_write_targets

    """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
    """
    def reserve_memory_regions(self, spec):
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region=self.SYSTEM_REGION,
                              size=self.SYSTEM_SIZE,
                              label='setup')
        
        spec.reserveMemRegion(region=self.PARAMS,
                              size=self.PARAMS_SIZE,
                              label='params')

    '''
    returns the maximum number of atoms needed for the multi-cast source
    '''
    def get_maximum_atoms_per_core(self):
        return 200 # each atom controls one agonist-antagonist muscle pair, we can register just 4 pairs

    '''
    returns the name of the model
    '''
    @property
    def model_name(self):
        return "Myorobot Motor Control"

    '''
    returns the resources of the multi-cast source
    '''
    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        return lib_map.Resources(0, 0, self.SYSTEM_SIZE + self.PARAMS_SIZE)

    '''
    overload component method and returns virtual chip key for routing info
    '''
    def generate_routing_info(self, subedge):
        x, y, p = subedge.postsubvertex.placement.processor.get_coordinates()
        key = packet_conversions.get_key_from_coords(x, y, p)
        return key, 0xfffff800
    
    def requires_multi_cast_source(self):
        return True    
        
    '''
    method that returns the commands for the retina external device
    '''
    def get_commands(self, last_runtime_tic):

        mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                   self.virtual_chip_coords['y'] << 16 | \
                   0 << 11
                   
        dummy_cmd = { 't': 0, 'cp': 1, 'repeat': 1, 'delay': 2,
                         'key': mgmt_key,
                         'payload': 0 } 

        commands = [dummy_cmd] # workaround weird handling of this setup stuff
                               # TODO: check the interdependency with multi_cast_source

        command = { 't': 1, 'cp': 1, 'repeat': 3, 'delay': 2,
                    'key': mgmt_key | 0x07F1,
                    'payload': 4 } # cmd to enable CAN hardware of spiNN-IO
        if self.myoID == 0:
            commands.append(command.copy()) # register only if I am the first user

        command['t'] = 2 + self.myoID # might not be important, but let's time-shift individual myos like this
        command['key'] = mgmt_key| 0x380 | self.myoID
        command['payload'] = (self.monitorCANID << 16) | self.motorCANID
        commands.append(command.copy()) # register muscle at id= myoID, t = 1 + myoID

        if self.myoID <= 1: # hard code setup of sensor here, as it does not currently fit elsewhere
            command['t'] = 3 + self.myoID 
            command['key'] = mgmt_key | 0x3C0 | self.myoID # note that myoID=1 is actually set-point
            command['payload'] = 0x50
            commands.append(command.copy())
            
            command['t'] = last_runtime_tic - 99 + self.myoID
            command['payload'] = 0
            commands.append(command.copy())
        
        command['t'] = last_runtime_tic-100 + self.myoID
        command['payload'] = 0
        commands.append(command.copy()) # deregister muscle before end (is that useful?)

        command['t'] = last_runtime_tic - 101 + self.myoID
        command['key'] = mgmt_key | 0x390 | self.myoID
        commands.append(command.copy()) # before deregistering: turn off motor.
        
        command['t'] = 3 + self.myoID
        command['key'] = mgmt_key | 0x3B0 | self.myoID
        command['payload'] = self.enableSensors
        commands.append(command.copy()) # register sensor streams according to enableSensors mask

        command['t'] = last_runtime_tic - 110 + self.myoID
        command['payload'] = 0
        commands.append(command.copy()) # switch off sensor streams (before deregistering)
        
        return commands
