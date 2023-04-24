
# Import major classes

from dronesim.types import *
from dronesim.app import SimulatorApplication, Panda3DEnvironment
from dronesim.actor import VehicleModel, UAVDroneModel
from dronesim.interface.default import DefaultDroneControl
from dronesim.interface import IDroneControllable, DroneAction, DroneState
from dronesim.simulator import DroneSimulator

from typing import Tuple


def make_uav() -> Tuple[DroneSimulator, IDroneControllable, VehicleModel]:
    '''Simple method to create a UAV model with a simulator attached'''
    sim = DroneSimulator()
    controller = DefaultDroneControl(sim)
    uav = UAVDroneModel(controller)
    return sim, controller, uav
