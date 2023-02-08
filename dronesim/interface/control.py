from abc import ABC

from ..types import StepRC, DroneAction
from typing import Any

class IDroneControllable(ABC):
    '''
    Abstract class to be able to call drone commands and retrieve status information.
    One can implement these methods to perform these actions within the simulated environment,
    or even interface with a real drone!
    '''

    ## Low-level interface functions ##

    def rc_control(self, vector : StepRC):
        '''Send direct RC control command with 3D movement velocity and yaw velocity control'''
        pass
    def get_current_state(self) -> Any:
        '''Returns the instantaneous state object. Type and format depends on the interface used'''
        pass
    def get_debug_data(self) -> dict:
        '''Returns `dict` with data to be used for debugging (eg. calibration data)'''
        return {}
    def direct_action(self, action : DroneAction, **params):
        '''Send `DroneAction` with optional parameters'''
        pass

    ## High-level interface functions ##
    # These functions can optionally block till the action completes, or timeout occurs

    def takeoff(self, blocking=True, timeout=None):
        '''Perform takeoff routine at the UAV's default hover altitude (1m in most cases)'''
        pass
    def land(self, blocking=True, timeout=None):
        '''Perform landing routine till UAV reaches ground level and motors stop'''
        pass
    def move_left(self, x : float, blocking=True, timeout=None):
        '''Strafe left direction (-ve X axis relative to UAV angle) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def move_right(self, x : float, blocking=True, timeout=None):
        '''Strafe right direction (+ve X axis relative to UAV angle) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def move_forward(self, x : float, blocking=True, timeout=None):
        '''Strafe front direction (+ve Y axis relative to UAV angle) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def move_backward(self, x : float, blocking=True, timeout=None):
        '''Strafe back direction (-ve Y axis relative to UAV angle) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def move_up(self, x : float, blocking=True, timeout=None):
        '''Increase altitude (+ve Z axis) with velocity `x` (between 0.0 - 1.0). Stops if highest flight altitude is achieved'''
        pass
    def move_down(self, x : float, blocking=True, timeout=None):
        '''Decrease altitude (-ve Z axis) with velocity `x` (between 0.0 - 1.0). Stops if lowest flight altitude is achieved'''
        pass
    def rotate_clockwise(self, x : float, blocking=True, timeout=None):
        '''Rotate UAV clockwise (along Z axis) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def rotate_counterclockwise(self, x : float, blocking=True, timeout=None):
        '''Rotate UAV counter-clockwise (along Z axis) with velocity `x` (between 0.0 - 1.0)'''
        pass
    def freeze(self, blocking=True, timeout=None):
        '''Completely stop horizontal motion (X-Y axis) and stay in place'''
        pass
