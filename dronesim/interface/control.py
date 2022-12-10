from abc import ABC

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
    def rc_control(self,
        left_right_velocity: int = None,
        forward_backward_velocity: int = None,
        up_down_velocity: int = None,
        yaw_velocity: int = None):
        pass
    def get_current_state(self):
        pass
    def move_left(self, x : int):
        pass
    def move_right(self, x : int):
        pass
    def move_up(self, x : int):
        pass
    def move_down(self, x : int):
        pass
    def rotate_clockwise(self, x : int):
        pass
    def rotate_counterclockwise(self, x : int):
        pass
    def freeze(self):
        pass
