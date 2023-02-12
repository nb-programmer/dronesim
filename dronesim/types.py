
'''Type aliases for use in the simulator'''

import typing
from .interface.action import DroneAction

Vec3Tuple = typing.Tuple[float, float, float]
Vec4Tuple = typing.Tuple[float, float, float, float]
PhysicsStateType = typing.Dict[str, typing.Any]

class SimulatorStateInfo(typing.TypedDict):
    state : PhysicsStateType
    metrics : dict
    sensors : dict

#State (observation) type returned by the step function, based on Gym: (observation, reward, done?, info)
StateType = typing.Tuple[typing.Any, float, bool, SimulatorStateInfo]
#Standard 4-value RC input (xyz velocity and yaw velocity)
StepRC = typing.NamedTuple("StepRC", velx=float, vely=float, velz=float, velr=float)

class StepAction(typing.TypedDict):
    rc : StepRC
    action : DroneAction
    params : dict

#StepAction in terms of tuple (RC vector) or dict containing parameters
StepActionType = typing.Union[StepRC, tuple, DroneAction, StepAction]

class InputState(typing.TypedDict):
    '''Input button/axis state (keyboard button held, joystick axis, etc.) that affects the UAV or camera'''
    movement_vec : StepRC
    is_jump_pressed : bool
    is_crouch_pressed : bool
    is_dash : bool
