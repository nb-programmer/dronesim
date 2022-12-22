from abc import ABC

from ..types import StepRC, DroneAction

class IDroneControllable(ABC):
    '''
    Abstract class to be able to call drone commands and retrieve status information.
    One can implement these methods to perform these actions within the simulated environment,
    or even interface with a real drone!
    '''

    def takeoff(self):
        pass
    def land(self):
        pass
    def rc_control(self, vector : StepRC):
        pass
    def get_current_state(self):
        pass
    def move_left(self, x : float):
        pass
    def move_right(self, x : float):
        pass
    def move_up(self, x : float):
        pass
    def move_down(self, x : float):
        pass
    def rotate_clockwise(self, x : float):
        pass
    def rotate_counterclockwise(self, x : float):
        pass
    def freeze(self):
        pass
    def directAction(self, action : DroneAction, args : dict = None):
        pass
