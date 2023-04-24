
from abc import ABC, abstractmethod

from .action import DroneAction
from .types import StepRC
from typing import Any, Optional


class UnsupportedAction(Exception):
    pass


class IDroneControllable(ABC):
    '''
    Abstract class to be able to call drone commands and retrieve status information.
    One can implement these methods to perform these actions within the simulated environment,
    or even interface with a real drone!
    '''

    ## Low-level interface functions ##

    @abstractmethod
    def rc_control(self, vector: StepRC):
        '''Send direct RC control command with 3D movement velocity and yaw velocity control'''
        pass

    @abstractmethod
    def get_current_state(self) -> Any:
        '''Returns the instantaneous state object. Type and format depends on the interface used'''
        pass

    @abstractmethod
    def get_debug_data(self) -> dict:
        '''Returns `dict` with data to be used for debugging (eg. calibration data)'''
        return {}

    @abstractmethod
    def direct_action(self, action: DroneAction, **params):
        '''Send `DroneAction` with optional parameters'''
        pass

    ## High-level interface functions ##
    # These functions can optionally block till the action completes, or timeout occurs

    @abstractmethod
    def arm(self, blocking=True, timeout=None):
        '''Prepare and unblock the motors so that flight can be achieved'''
        pass

    @abstractmethod
    def unarm(self, blocking=True, timeout=None):
        '''Block the motors and stop them (after landing!) so that they don't run accidentally'''
        pass

    @abstractmethod
    def takeoff(self, blocking=True, timeout=None):
        '''Perform takeoff routine at the UAV's default hover altitude (1m in most cases)'''
        raise UnsupportedAction()

    @abstractmethod
    def land(self, blocking=True, timeout=None):
        '''Perform landing routine till UAV reaches ground level and motors stop'''
        raise UnsupportedAction()

    @abstractmethod
    def move_left(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Strafe left direction (-ve X axis relative to UAV angle) `x` units with speed `s` units per unit time (must be positive)'''
        pass

    @abstractmethod
    def move_right(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Strafe right direction (+ve X axis relative to UAV angle) `x` units with speed `s` units per unit time (must be positive)'''
        pass

    @abstractmethod
    def move_forward(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Strafe front direction (+ve Y axis relative to UAV angle) `x` units with speed `s` units per unit time (must be positive)'''
        pass

    @abstractmethod
    def move_backward(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Strafe back direction (-ve Y axis relative to UAV angle) `x` units with speed `s` units per unit time (must be positive)'''
        pass

    @abstractmethod
    def move_up(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Increase altitude (+ve Z axis) by `x` units with speed `s` units per unit time (must be positive). Stops if highest flight altitude is achieved'''
        raise UnsupportedAction()

    @abstractmethod
    def move_down(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Decrease altitude (-ve Z axis) by `x` units with speed `s` units per unit time (must be positive). Stops if lowest flight altitude is achieved'''
        raise UnsupportedAction()

    @abstractmethod
    def rotate_clockwise(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Rotate UAV clockwise (along Z axis) `x` degrees with speed `s` degrees per unit time (must be positive) (360 is a full rotation, 720 is two rotations, etc.)'''
        pass

    @abstractmethod
    def rotate_counterclockwise(self, x: float, s: Optional[float] = None, blocking=True, timeout=None):
        '''Rotate UAV counter-clockwise (along Z axis) `x` degrees with speed `s` degrees per unit time (must be positive) (360 is a full rotation, 720 is two rotations, etc.)'''
        pass

    @abstractmethod
    def freeze(self, blocking=True, timeout=None):
        '''Completely stop horizontal motion (X-Y axis) and stay in place'''
        pass


__all__ = [
    'UnsupportedAction',
    'IDroneControllable'
]
