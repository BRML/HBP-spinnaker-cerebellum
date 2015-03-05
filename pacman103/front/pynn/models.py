from pacman103.front import common

class IF_curr_exp( common.IF_CurrentExponentialPopulation ):
    pass

class IF_curr_dual_exp( common.IF_CurrentDualExponentialPopulation ):
    pass

class IF_cond_exp( common.IF_ConductanceExponentialPopulation ):
    pass

class IZK_curr_exp( common.Izhikevich_CurrentExponentialPopulation ):
    pass

class SpikeSourceArray( common.SpikeSourceArray ):
    pass

class SpikeSourcePoisson( common.SpikeSourcePoisson ):
    pass

class SpikeSourceRemote( common.SpikeSourceRemote ):
    pass

class ExternalCochleaDevice(common.ExternalCochleaDevice):
    pass

class ExternalRetinaDevice(common.ExternalRetinaDevice):
    pass

class ExternalMotorDevice(common.ExternalMotorDevice):
    pass

class MultiCastSource(common.MultiCastSource):
    pass

class RobotMotorControl(common.RobotMotorControl):
    pass

class MyoRobotMotorControl(common.MyoRobotMotorControl):
    pass

class ExternalFPGARetinaDevice(common.ExternalFPGARetinaDevice):
    pass

class ExternalSpikeSource(common.ExternalSpikeSource):
    pass
