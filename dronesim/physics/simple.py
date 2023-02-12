
from .physicsbase import DronePhysicsEngine, Vec4PID
from ..interface import DroneAction, DroneState
from ..types import StepActionType, StepRC, PhysicsStateType

from simple_pid import PID
import glm

import typing

class SimpleDronePhysics(DronePhysicsEngine):
    '''
    Not really that simple :)

    Assume units are in centimeters when translating to irl unit
    '''

    GRAVITY = glm.vec3(0, 0, -2e-1)
    AIR_RESISTANCE = glm.vec3((0.98,)*3)

    #How many ticks to continue with the previously received command if no command is given the subsequent ticks
    REPEAT_MISSING_STEP_TICKS = 30

    #RC_SCALE will get multiplied by each input RC vector component
    #Angle is counter-clockwise from 3 o'clock position, so negate the magnitude to turn properly
    RC_SCALE = glm.vec4(0.2, 0.2, 0.1, -0.05)

    TAKEOFF_COMPLETE_ERROR_MAX = 1e-1
    ARMED_MIN_THRUST = 1e-3
    TAKEOFF_COMPLETE_STABLE_TICKS = 30

    #PID controller parameters
    STRAFE_CONTROL_PARAM = {'Kp': 0.02, 'Ki': 0.0, 'Kd': 0.0}
    LIFT_CONTROL_PARAM = {'Kp': 0.019, 'Ki': 0.012, 'Kd': 0.0}
    TURN_CONTROL_PARAM = {'Kp': 0.2, 'Ki': 0.0, 'Kd': 0.0}

    class State(dict):
        def __init__(self, init_state : dict = None):
            super().__init__()

            #Apply default state. PID default coefficients may not work
            #so you will need to provide your own PID values in the init_state

            #Position of the drone in 3D-space
            self['pos'] = glm.vec3(0,0,0)
            #Facing orientation in 3D-space
            self['angle'] = glm.vec3(0,0,0)

            #Instantaneous velocity. 4D vector for matrix transformation
            self['pvel'] = glm.vec4(0,0,0,1)
            self['fvel'] = glm.vec3()
            self['avel'] = glm.vec3()

            #Tick counters
            self['ticks'] = 0
            self['_lastRC'] = None
            self['_tickLogs'] = {}

            #Thrust to apply
            self['thrust_vec'] = glm.vec3()

            #Landed, stationary
            self['operation'] = DroneState.LANDED

            #Movement PID control. XY and W is for velocity, Z is for absolute position (altitude)
            self['control'] = Vec4PID(*(PID(sample_time=None) for _ in range(4)))

            if init_state is not None:
                self.update(init_state)

    def reset(self, state : typing.Union[State, PhysicsStateType] = None) -> State:
        if state is None:
            state = {}
        if 'control' not in state:
            target_z = 0
            if 'pos' in state:
                target_z = state['pos'].z
            #Apply different PID parameters than default
            state.update({
                'control': Vec4PID(
                    PID(**self.STRAFE_CONTROL_PARAM, sample_time=None),
                    PID(**self.STRAFE_CONTROL_PARAM, sample_time=None),
                    PID(**self.LIFT_CONTROL_PARAM,   sample_time=None, setpoint=target_z),
                    PID(**self.TURN_CONTROL_PARAM,   sample_time=None)
                )
            })
        self._state : PhysicsStateType = SimpleDronePhysics.State(state)
        return self._state

    def get_debug_data(self) -> dict:
        return {
            'pos': self._state['pos'],
            'angle': self._state['angle'],
            'absvel': self._state['pvel'].xyz,
            'relvel': self._state['fvel'],
            'thrust': self._state['thrust_vec'],
            'setpoint': glm.vec4(
                self._state['control'].x.setpoint,
                self._state['control'].y.setpoint,
                self._state['control'].z.setpoint,
                self._state['control'].w.setpoint
            ),
            'operation': self._state['operation']
        }

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self.reset(state)

    @property
    def operation(self):
        return self._state['operation']

    def step(self, action : StepActionType, dt : float = None) -> State:
        '''Update the physics engine'''
        #NOTE: If dt is None, the PID controller choses to use real-time dt. Use fixed value dt to make it repeatable.

        self._state['ticks'] += 1

        rcvec, op, params = self.decode_action(action)

        _prev_op = self._state['operation']

        #State machine
        if op is not None:
            if op == DroneAction.TAKEOFF:
                if self._state['operation'] == DroneState.LANDED:
                    self._state['operation'] = DroneState.TAKING_OFF
                    self._state['control'].z.setpoint = params.get("altitude", 10.0)
                    self._state['_tickLogs'][DroneState.TAKING_OFF] = 0

        if self._state['operation'] == DroneState.TAKING_OFF:
            z_error = self._state['control'].z.setpoint - self._state['pos'].z
            abs_speed = glm.length(self._state['pvel'].xyz)
            #print(abs_speed)
            if abs(z_error) < self.TAKEOFF_COMPLETE_ERROR_MAX:
                self._state['_tickLogs'][DroneState.TAKING_OFF] += 1
                if self._state['_tickLogs'][DroneState.TAKING_OFF] > self.TAKEOFF_COMPLETE_STABLE_TICKS:
                    self._state['operation'] = DroneState.IN_AIR

        #Emit operation change event
        if self._state['operation'] != _prev_op:
            self.emit('operation', self._state['operation'])

        #Save last RC for later
        if rcvec is not None:
            self._state['_lastRC'] = (rcvec, self._state['ticks'])
        #If no RC, reuse previous RC input for some steps
        else:
            #TODO: Allow this behaviour to be optional
            if self._state['_lastRC'] is not None and self._state['_lastRC'][0] is not None and self._state['ticks'] < self._state['_lastRC'][1] + self.REPEAT_MISSING_STEP_TICKS:
                rcvec = self._state['_lastRC'][0]
            else:
                rcvec = StepRC(0,0,0,0)

        #Which direction to move using RC
        rc_vec = glm.vec4(rcvec)
        rc_vec = glm.clamp(rc_vec, -1, 1)
        rc_vec *= self.RC_SCALE

        is_on_surface = False
        is_armed = self._state['operation'] != DroneState.LANDED
        is_accept_rc = self._state['operation'] == DroneState.IN_AIR

        #RC thrust control
        if is_accept_rc:
            self._state['control'].x.setpoint = rc_vec.x  # Target velocity
            self._state['control'].y.setpoint = rc_vec.y  # Target velocity
            self._state['control'].w.setpoint = rc_vec.w  # Target heading angle velocity
            self._state['control'].z.setpoint += rc_vec.z # Absolute height
            if self._state['control'].z.setpoint < 0:
                self._state['control'].z.setpoint = 0.0

        #Apply thrust based on target position
        self._state['thrust_vec'].x = self._state['control'].x(self._state['pvel'].x, dt)
        self._state['thrust_vec'].y = self._state['control'].y(self._state['pvel'].y, dt)
        self._state['thrust_vec'].z = glm.max(self._state['control'].z(self._state['pos'].z, dt), self.ARMED_MIN_THRUST if is_armed else 0.0)
        self._state['avel'].z = self._state['control'].w(self._state['avel'].z, dt)
        
        #3D coordinate transformation matrix
        tfmat = glm.mat4()

        tfmat = glm.translate(tfmat, self._state['thrust_vec'])
        tfmat = glm.translate(tfmat, self.GRAVITY)
        tfmat = glm.scale(tfmat, self.AIR_RESISTANCE)

        #Update velocity vector
        self._state['pvel'] = tfmat * self._state['pvel']

        #Rotate view
        self._state['angle'] += self._state['avel']

        #Velocity vector in current facing direction
        vel_facing = glm.rotate(self._state['pvel'].xyz, self._state['angle'].z, glm.vec3(0,0,1))

        #Move position 
        self._state['pos'] += vel_facing

        #Hit ground
        if self._state['pos'].z < 0.0:
            #Reset velocity to 0 and position to ground
            self._state['pos'].z = 0.0
            self._state['pvel'].z = 0.0

        return self._state
