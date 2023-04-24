
from simple_pid import PID

from dronesim.interface import DroneAction, DroneState

import pyee

from dronesim.types import StepActionType, StepRC, PhysicsStateType
from typing import Optional, Tuple, NamedTuple


# 4-dimension PID control
Vec4PID = NamedTuple('VEC4DOFPID', x=PID, y=PID, z=PID, w=PID)


class DronePhysicsEngine(pyee.EventEmitter):
    '''
    Physics engine base class (abstract class) used to implement UAV physics engines for simulation.

    Note that pyee's EventEmitter is used as the event manager. If you want to make use a different method
    to handle events, such as using asyncio's coroutines, you can `uplift` method (pyee.uplift.uplift) to convert
    the simulator class to the desired emitter type.
    '''

    def __init__(self):
        super().__init__()
        self.__state: PhysicsStateType = {}

    @staticmethod
    def decode_action(action: StepActionType) -> Tuple[Optional[StepRC], Optional[DroneAction], dict]:
        # We want to use StepRC for the movement
        rcvec: StepRC = None
        # Operation to perform actions (takeoff, land, tricks, etc)
        op: DroneAction = None
        # Params of the operation, if any
        params: dict = {}

        # If action is None or unknown type, above values are returned, the physics engine may interpret
        # them as desired, such as performing previous action, having no action (halt in place)

        if isinstance(action, StepRC):
            # Just RC is given directly
            rcvec = action
        elif isinstance(action, tuple):
            # Tuple with values of RC is given, cast to StepRC
            rcvec = StepRC(*action)
        elif isinstance(action, DroneAction):
            # Just DroneAction is given directly without any params
            op = action
        elif isinstance(action, dict):
            # Dict with various data is given (StepType-based dict)
            rcvec = action.pop('rc', None)
            op = action.pop('action', None)
            params.update(action.pop('params', {}))

        return rcvec, op, params

    @property
    def operation(self): return DroneState.LANDED

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        raise NotImplementedError(
            "%s does not support setting state" % self.__class__.__name__)

    def reset(self, state: Optional[PhysicsStateType] = None) -> PhysicsStateType:
        raise NotImplementedError()

    def step(self, action: StepActionType, dt: float = None) -> PhysicsStateType:
        raise NotImplementedError()

    def get_debug_data(self) -> dict:
        return {}
