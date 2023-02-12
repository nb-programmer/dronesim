
import os
import typing
PACKAGE_BASE = os.path.normpath(os.path.dirname(__file__))

#Import major classes
from dronesim.simulator import DroneSimulator
from dronesim.interface import IDroneControllable, DroneAction, DroneState
from dronesim.interface.default import DefaultDroneControl
from dronesim.actor import UAVDroneModel
from dronesim.simapp import SimulatorApplication

def make_uav() -> typing.Tuple[DroneSimulator, IDroneControllable, UAVDroneModel]:
    '''Simple method to create a UAV model with a simulator attached'''
    sim = DroneSimulator()
    controller = DefaultDroneControl(sim)
    uav = UAVDroneModel(controller)
    return sim, controller, uav
