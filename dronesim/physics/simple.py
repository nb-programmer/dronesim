
from simple_pid import PID
import glm

from .physicsbase import DronePhysicsEngine, PhysicsStateType, Vec4PID
from ..types import DroneState, DroneAction, StepActionType, StepRC

class SimpleDronePhysics(DronePhysicsEngine):
    '''
    Not really that simple :)

    Assume units are in centimeters when translating to irl unit
    '''
    
    GRAVITY = glm.vec3(0, 0, -2e-1)
    AIR_RESISTANCE = glm.vec3((0.98,)*3)
    #Angle is counter-clockwise from 3 o'clock position, so negate the magnitude to turn properly
    RC_SCALE = glm.vec4(0.2, 0.2, 0.1, -0.05)

    TAKEOFF_COMPLETE_ERROR_MAX = 1e-1
    ARMED_MIN_THRUST = 1e-3
    TAKEOFF_COMPLETE_STABLE_TICKS = 30
    
    #PID controller parameters
    STRAFE_CONTROL_PARAM = {'Kp': 0.02, 'Ki': 0.0, 'Kd': 0.0}
    LIFT_CONTROL_PARAM = {'Kp': 0.019, 'Ki': 0.012, 'Kd': 0.0}
    TURN_CONTROL_PARAM = {'Kp': 0.2, 'Ki': 0.0, 'Kd': 0.0}

    def reset(self, state : PhysicsStateType = None) -> PhysicsStateType:
        #TODO: put all of this in a dict-inheriting class and use that as state

        #Position of the drone in space
        self.pos = glm.vec3((0,0,0))
        self.angle = glm.vec3((0,0,0))
        #Instantaneous velocity
        self.pvel = glm.vec4(0,0,0,1)
        self.fvel = glm.vec3()
        self.avel = glm.vec3()
        self.ticks = 0
        self._lastRC = None
        self._tickLogs : dict = {}

        #Thrust to apply
        self.thrust_vec = glm.vec3()

        #Landed, stationary
        self._operation = DroneState.LANDED

        #Movement PID control. XY and W is for velocity, Z is for absolute position (altitude)
        self.control = Vec4PID(
            PID(**self.STRAFE_CONTROL_PARAM, sample_time=None),
            PID(**self.STRAFE_CONTROL_PARAM, sample_time=None),
            PID(**self.LIFT_CONTROL_PARAM,   sample_time=None, setpoint=self.pos.z),
            PID(**self.TURN_CONTROL_PARAM,   sample_time=None)
        )

        self._state : PhysicsStateType = dict()
        self._updateState()

        return self.state

    def _updateState(self):
        self._state.update({
            'pos': self.pos,
            'angle': self.angle,
            'absvel': self.pvel.xyz,
            'relvel': self.fvel,
            'thrust': self.thrust_vec,
            'setpoint': glm.vec4(
                self.control.x.setpoint,
                self.control.y.setpoint,
                self.control.z.setpoint,
                self.control.w.setpoint
            ),
            'operation': self._operation
        })
        return self._state
    
    @property
    def state(self): return self._state

    @state.setter
    def state(self, state):
        print("Set state", state)
        self.reset(state)

    def step(self, action : StepActionType, dt : float = None) -> PhysicsStateType:
        self.ticks += 1

        rcvec, op, params = self.decodeAction(action)

        #State machine
        if op is not None:
            if op == DroneAction.TAKEOFF:
                if self._operation == DroneState.LANDED:
                    self._operation = DroneState.TAKING_OFF
                    self.control.z.setpoint = params.get("altitude", 10.0)
                    self._tickLogs[DroneState.TAKING_OFF] = 0

        if self._operation == DroneState.TAKING_OFF:
            z_error = self.control.z.setpoint - self.pos.z
            abs_speed = glm.length(self.pvel.xyz)
            #print(abs_speed)
            if abs(z_error) < self.TAKEOFF_COMPLETE_ERROR_MAX:
                self._tickLogs[DroneState.TAKING_OFF] += 1
                if self._tickLogs[DroneState.TAKING_OFF] > self.TAKEOFF_COMPLETE_STABLE_TICKS:
                    self._operation = DroneState.IN_AIR

        #Save last RC for later
        if rcvec is not None:
            self._lastRC = (rcvec, self.ticks)
        #If no RC, reuse previous RC input for some steps
        else:
            if self._lastRC is not None and self._lastRC[0] is not None and self.ticks < self._lastRC[1] + 30:
                rcvec = self._lastRC[0]
            else:
                rcvec = StepRC(0,0,0,0)

        #Which direction to move using RC
        rc_vec = glm.vec4(rcvec)
        rc_vec = glm.clamp(rc_vec, -1, 1)
        rc_vec *= self.RC_SCALE

        is_on_surface = False
        is_armed = self._operation != DroneState.LANDED
        is_accept_rc = self._operation == DroneState.IN_AIR

        #RC thrust control
        if is_accept_rc:
            self.control.x.setpoint = rc_vec.x  # Target velocity
            self.control.y.setpoint = rc_vec.y  # Target velocity
            self.control.w.setpoint = rc_vec.w  # Target heading angle
            self.control.z.setpoint += rc_vec.z # Absolute height
            if self.control.z.setpoint < 0:
                self.control.z.setpoint = 0.0

        #Apply thrust based on target position
        self.thrust_vec.x = self.control.x(self.pvel.x, dt)
        self.thrust_vec.y = self.control.y(self.pvel.y, dt)
        self.thrust_vec.z = glm.max(self.control.z(self.pos.z, dt), self.ARMED_MIN_THRUST if is_armed else 0.0)
        self.avel.z = self.control.w(self.avel.z, dt)
        
        #3D coordinate transformation matrix
        tfmat = glm.mat4()

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

        #Hit ground
        if self.pos.z < 0.0:
            #Reset velocity to 0 and position to ground
            self.pos.z = 0.0
            self.pvel.z = 0.0

        #print("(", self.pos.x, self.pos.y, self.pos.z, ")", self.pvel.z)
        
        #Reflect data to state
        return self._updateState()

