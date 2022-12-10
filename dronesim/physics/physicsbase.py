
import typing

from simple_pid import PID

from ..types import DroneState, StepActionType, DroneAction, StepRC

#4-dimension PID control
Vec4PID = typing.NamedTuple('VEC4DOFPID', x=PID, y=PID, z=PID, w=PID)
PhysicsStateType = typing.Dict[str, typing.Any]

class DronePhysicsEngine:
    def __init__(self):
        #Current operation: Landed state
        self._operation : DroneState = DroneState.LANDED
        #No state data yet. Will only be set after a reset
        self._state = None
        
    @staticmethod
    def decodeAction(action : StepActionType):
        #We want to use StepRC for the movement
        rcvec = None
        #Operation to perform actions (takeoff, land, tricks, etc)
        op : DroneAction = None
        #Params of the operation, if any
        params : dict = {}

        if isinstance(action, StepRC):
            #Just RC is given directly
            rcvec = action
        elif isinstance(action, tuple):
            #Tuple with values of RC is given
            rcvec = StepRC(*action)
        elif isinstance(action, dict):
            #Dict with various data is given
            rcvec = StepRC(*action.pop('rc', StepRC(0,0,0,0)))
            op = action.pop('action', None)
            params.update(action)
            
        return rcvec, op, params

    @property
    def operation(self): return self._operation
    @property
    def state(self): return self._state
    @state.setter
    def state(self, state): raise NotImplementedError("%s does not support setting state" % self.__class__.__name__)

    def reset(self, state = None) -> typing.Any:
        self._state : PhysicsStateType = state
        return self._state
    def step(self, action : StepActionType, dt : float = None) -> typing.Any:
        raise NotImplementedError()

