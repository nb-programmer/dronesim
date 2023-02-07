
import os
import typing
PACKAGE_BASE = os.path.normpath(os.path.dirname(__file__))

#Import major classes
from dronesim.simulator import DroneSimulator
from dronesim.types import DroneState
from dronesim.interface import IDroneControllable, DefaultDroneControl
from dronesim.actor import UAVDroneModel

def make_uav() -> typing.Tuple[DroneSimulator, IDroneControllable, UAVDroneModel]:
    '''Simple method to create a UAV model with a simulator attached'''
    sim = DroneSimulator()
    controller = DefaultDroneControl(sim)
    uav = UAVDroneModel(controller)
    return sim, controller, uav
