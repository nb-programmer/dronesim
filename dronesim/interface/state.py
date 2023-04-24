
from enum import Enum, auto


class DroneState(Enum):
    '''UAV's current state of operation. Can be extended to add more states'''
    LANDING = auto()
    LANDED = auto()
    TAKING_OFF = auto()
    IN_AIR = auto()
