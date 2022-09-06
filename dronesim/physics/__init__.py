
import typing

import numpy as np
from simple_pid import PID
import glm

from dronesim.utils import DroneState, StepAction, StepActionType

#4-dimension PID control
Vec4PID = typing.NamedTuple('VEC4DOFPID', x=PID, y=PID, z=PID, w=PID)
PhysicsStateType = typing.Dict[str, typing.Any]

class DronePhysicsEngine:
    def __init__(self):
        #Current operation: Landed state
        self._operation : DroneState = DroneState.LANDED
        #No state data yet. Will only be set after a reset
        self._state = None

    def _toStepAction(self, action : StepActionType):
        return action if isinstance(action, StepAction) else StepAction(*action)

    @property
    def operation(self): return self._operation
    @property
    def state(self): return self._state

    def reset(self, *args, **kwargs) -> typing.Any:
        self._state : PhysicsStateType = {'pos': (0,0,0)}
        return self._state
    def step(self, action : typing.Union[StepActionType, typing.Any], dt : float = None) -> typing.Any: raise NotImplementedError()
    def takeoff(self): raise NotImplementedError()
    def land(self): raise NotImplementedError()

class SimpleDronePhysics(DronePhysicsEngine):
    '''
    Not really that simple :)
    '''
    
    GRAVITY = glm.vec3(0, 0, -1e-3)
    AIR_RESISTANCE = glm.vec3((0.95,)*3)
    #Angle is counter-clockwise from 3 o'clock position, so negate the magnitude to turn properly
    RC_SCALE = glm.vec4(0.009, 0.009, 0.005, -0.018)
    
    #PID controller parameters
    STRAFE_CONTROL_PARAM = {'Kp': 0.45, 'Ki': 0.01, 'Kd': 0.0}
    LIFT_CONTROL_PARAM = {'Kp': 0.002, 'Ki': 0.002, 'Kd': 0.0}
    TURN_CONTROL_PARAM = {'Kp': 0.99, 'Ki': 0.01, 'Kd': 0.0}

    def reset(self, start_pos : np.ndarray, start_rot : np.ndarray) -> PhysicsStateType:
        #Position of the drone in space
        self.pos = glm.vec3(start_pos)
        self.angle = glm.vec3(start_rot)
        #Instantaneous velocity
        self.pvel = glm.vec4(0,0,0,1)
        self.fvel = glm.vec3()
        self.avel = glm.vec3()

        #Thrust to apply
        self.thrust_vec = glm.vec3()

        #Movement PID control. XY and W is for velocity, Z is for absolute position (altitude)
        self.control = Vec4PID(
            PID(**self.STRAFE_CONTROL_PARAM),
            PID(**self.STRAFE_CONTROL_PARAM),
            PID(**self.LIFT_CONTROL_PARAM, setpoint=self.pos.z),
            PID(**self.TURN_CONTROL_PARAM)
        )

        self._updateState()

        #Landed, stationary
        self._operation = DroneState.LANDED

        return self.state

    def _updateState(self):
        self._state : PhysicsStateType = {
            'pos': self.pos,
            'angle': self.angle,
            'absvel': self.pvel.xyz,
            'relvel': self.fvel
        }
        return self.state

    def step(self, action : StepAction, dt : float = None) -> PhysicsStateType:
        #We want to use only StepAction for this engine
        action = self._toStepAction(action)

        #3D coordinate transformation matrix
        tfmat = glm.mat4()

        #Which direction to move using RC
        rc_vec = glm.vec4(action)
        rc_vec = glm.clamp(rc_vec, -1, 1)
        rc_vec *= self.RC_SCALE

        is_on_surface = False
        is_accept_rc = False

        #RC thrust control
        self.control.x.setpoint = rc_vec.x
        self.control.y.setpoint = rc_vec.y
        self.control.w.setpoint = rc_vec.w
        self.control.z.setpoint += rc_vec.z

        #Apply thrust based on target position
        self.thrust_vec.x = self.control.x(self.pvel.x, dt)
        self.thrust_vec.y = self.control.y(self.pvel.y, dt)
        self.thrust_vec.z = self.control.z(self.pos.z, dt)
        self.avel.z = self.control.w(self.avel.z, dt)

        tfmat = glm.translate(tfmat, self.thrust_vec)
        tfmat = glm.translate(tfmat, self.GRAVITY)
        tfmat = glm.scale(tfmat, self.AIR_RESISTANCE)

        #Update velocity vector
        self.pvel = tfmat * self.pvel

        #Rotate view
        self.angle += self.avel

        #Velocity vector in current facing direction
        vel_facing = glm.rotate(self.pvel.xyz, self.angle.z, glm.vec3(0,0,1))

        #Move position 
        self.pos += vel_facing

        #print(self.pos.z)

        #print(self.pvel.z, self.pos.z)

        #Hit ground
        if self.pos.z < 0.0:
            #Reset velocity to 0 and position to ground
            self.pos.z = 0.0
            self.pvel.z = 0.0

        #Reflect data to state
        return self._updateState()

    def takeoff(self):
        if self._operation == DroneState.LANDED:
            self._operation = DroneState.TAKING_OFF
            self.control.z.setpoint = 2.0

    def land(self):
        if self._operation == DroneState.IN_AIR or self._operation == DroneState.TAKING_OFF:
            self._operation = DroneState.LANDING
            self.control.z.setpoint = 0.3

