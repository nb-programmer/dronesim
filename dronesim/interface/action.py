
from enum import Enum, auto


class DroneAction(Enum):
    '''
    Action or operation the UAV has to perform (takeoff, land, flip, etc.).

    You can extend this class if your (custom) engine has a different set, but
    make sure to use the correct enum class for that!
    '''
    ARM = auto()
    UNARM = auto()
    TAKEOFF = auto()
    LAND = auto()
    STOP_IN_PLACE = auto()
    MOTOROFF = auto()
