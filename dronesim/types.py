
import typing
import enum

#Type aliases

Vec3Tuple = typing.Tuple[float, float, float]
Vec4Tuple = typing.Tuple[float, float, float, float]
#State (observation) type returned by the step function, based on Gym: (observation, reward, done?, info)
StateType = typing.Tuple[typing.Any, float, bool, typing.Dict[str, typing.Any]]
#Standard 4-value RC input (xyz velocity and yaw velocity)
StepRC = typing.NamedTuple("StepRC", velx=float, vely=float, velz=float, velr=float)
#StepAction in terms of tuple (RC vector) or dict containing parameters
StepActionType = typing.Union[StepRC, tuple, dict]

#Drone state and actions it can perform.
#TODO: Move to separate modules

class DroneState(enum.Enum):
    '''UAV's current state of operation. Can be extended to add more states'''
    LANDING = enum.auto()
    LANDED = enum.auto()
    ARMED = enum.auto()
    TAKING_OFF = enum.auto()
    IN_AIR = enum.auto()

class DroneAction(enum.Enum):
    TAKEOFF = enum.auto()
    LAND = enum.auto()
    STOP_IN_PLACE = enum.auto()
    MOTOROFF = enum.auto()
