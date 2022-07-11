
import time
import typing
import numpy as np
import enum

_last_check_time = {}
def callevery(check_every : float):
    def timed_func_call_wrap(func):
        _last_check_time[func.__qualname__] = [0.0, check_every, None]
        def _needs_call(name):
            return (len(_last_check_time[name]) < 3) or (time.time() - _last_check_time[name][0] > _last_check_time[name][1])
        def timed_func_call(*args, **kwargs):
            f_name = func.__qualname__
            if _needs_call(f_name):
                _last_check_time[f_name][2] = func(*args, **kwargs)
                _last_check_time[f_name][0] = time.time()
                return _last_check_time[f_name][2]
            return _last_check_time[f_name][2]
        return timed_func_call
    return timed_func_call_wrap


#State (observation) type returned by the step function, based on Gym: (observation, reward, done?, info)
StateType = typing.Tuple[typing.Any, int, bool, typing.Dict[str, typing.Any]]
#Standard 4-value RC input (xyz velocity and yaw velocity)
StepAction = typing.NamedTuple("StepAction", velx=float, vely=float, velz=float, velr=float)
#StepAction in terms of list, tuple or Numpy array
StepActionType = typing.Union[StepAction, typing.List, typing.Tuple, np.ndarray]

class DroneState(enum.Enum):
    LANDED = enum.auto()
    TAKING_OFF = enum.auto()
    IN_AIR = enum.auto()
    LANDING = enum.auto()
