
import typing
import enum

Vec3Tuple = typing.Tuple[float, float, float]
#State (observation) type returned by the step function, based on Gym: (observation, reward, done?, info)
StateType = typing.Tuple[typing.Any, float, bool, typing.Dict[str, typing.Any]]
#Standard 4-value RC input (xyz velocity and yaw velocity)
StepRC = typing.NamedTuple("StepRC", velx=float, vely=float, velz=float, velr=float)
#StepAction in terms of tuple (RC vector) or dict containing parameters
StepActionType = typing.Union[StepRC, tuple, dict]

class DroneState(enum.Enum):
    LANDING = enum.auto()
    LANDED = enum.auto()
    TAKING_OFF = enum.auto()
    IN_AIR = enum.auto()

class DroneAction(enum.Enum):
    TAKEOFF = enum.auto()
    LAND = enum.auto()
    STOPINPLACE = enum.auto()
    MOTOROFF = enum.auto()
