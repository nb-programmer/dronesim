
from .action import DroneAction
from typing import Union, TypedDict, NamedTuple


# Standard 4-value RC input (xyz velocity and yaw velocity)
StepRC = NamedTuple("StepRC", velx=float, vely=float, velz=float, velr=float)


class StepAction(TypedDict):
    rc: StepRC
    action: DroneAction
    params: dict


# StepAction in terms of tuple (RC vector) or dict containing parameters
StepActionType = Union[StepRC, tuple, DroneAction, StepAction]
