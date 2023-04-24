
'''Type aliases for use in the simulator'''

import os
from panda3d.core import Filename

from dronesim.interface.types import StepRC, StepAction, StepActionType

from typing import Union, Tuple, TypedDict, NamedTuple, Dict, Any


PandaFilePath = Union[str, os.PathLike, Filename]
Vec3Tuple = Tuple[float, float, float]
Vec4Tuple = Tuple[float, float, float, float]
PhysicsStateType = Dict[str, Any]


class SimulatorStateInfo(TypedDict):
    state: PhysicsStateType
    metrics: dict
    sensors: dict


# State (observation) type returned by the step function, based on Gym: (observation, reward, done?, info)
StateType = Tuple[Any, float, bool, SimulatorStateInfo]


class InputState(TypedDict):
    '''Input button/axis state (keyboard button held, joystick axis, etc.) that affects the Vehicle or camera'''
    movement_vec: StepRC
    is_jump_pressed: bool
    is_crouch_pressed: bool
    is_dash: bool


__all__ = [
    'PandaFilePath',
    'Vec3Tuple',
    'Vec4Tuple',
    'PhysicsStateType',
    'SimulatorStateInfo',
    'StateType',
    'StepRC',
    'StepAction',
    'StepActionType',
    'InputState'
]
