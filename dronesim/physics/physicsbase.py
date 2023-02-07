
import typing

from simple_pid import PID

from ..types import DroneState, StepActionType, DroneAction, StepRC

import pyee

#4-dimension PID control
Vec4PID = typing.NamedTuple('VEC4DOFPID', x=PID, y=PID, z=PID, w=PID)
PhysicsStateType = typing.Dict[str, typing.Any]

class DronePhysicsEngine(pyee.EventEmitter):
    '''
    Physics engine base class (abstract class) used to implement UAV physics engines for simulation.

    Note that pyee's EventEmitter is used as the event manager. If you want to make use a different method
    to handle events, such as using asyncio's coroutines, you can `uplift` method (pyee.uplift.uplift) to convert
    the simulator class to the desired emitter type.
    '''
    def __init__(self):
        super().__init__()
        #No state data yet. Will only be set after a reset
        self._state = None
        
    @staticmethod
    def decode_action(action : StepActionType):
        #We want to use StepRC for the movement
        rcvec = None
        #Operation to perform actions (takeoff, land, tricks, etc)
        op : DroneAction = None
        #Params of the operation, if any
        params : dict = {}

        #If action is None, above values are returned, the physics engine may interpret
        #them as desired, such as performing previous action, having no action (halt in place)

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
    def operation(self): return DroneState.LANDED
    @property
    def state(self): return self._state
    @state.setter
    def state(self, state): raise NotImplementedError("%s does not support setting state" % self.__class__.__name__)

    def reset(self, state = None) -> typing.Any:
        self._state : PhysicsStateType = state
        return self._state
    def step(self, action : StepActionType, dt : float = None) -> typing.Any:
        raise NotImplementedError()
    def get_debug_data(self) -> dict:
        return {}

