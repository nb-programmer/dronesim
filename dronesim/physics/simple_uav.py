
from .physicsbase import DronePhysicsEngine, Vec4PID
from ..interface import DroneAction, DroneState

# PID controller
from simple_pid import PID
import glm

from ..types import StepActionType, StepRC
from typing import Union, TypedDict, Dict


class SimplePhysicsStateType(TypedDict):
    '''Data type that will be used to provide state of current UAV operation'''
    # Whether motors are armed and is ready to fly
    motor_armed: bool

    # Position of the drone in 3D-space
    pos: glm.vec3
    # Facing orientation in 3D-space
    angle: glm.vec3

    # Instantaneous velocity. 4D vector for matrix transformation
    pvel: glm.vec4
    avel: glm.vec3

    # Tick counters
    ticks: int
    _lastRC: StepRC
    _tickLogs: Dict[DroneState, int]

    # Thrust to apply
    thrust_vec: glm.vec3

    # Landed, stationary
    operation: DroneState

    # Movement PID control. XY and W is for velocity, Z is for absolute position (altitude)
    control: Vec4PID


class SimpleUAVDronePhysics(DronePhysicsEngine):
    '''
    Not really that simple :)

    Assume units are in centimeters when translating to irl unit (that's what I did in the models)
    '''

    GRAVITY = glm.vec3(0, 0, -2e-1)
    AIR_RESISTANCE = glm.vec3((0.98,)*3)

    # How many ticks to continue with the previously received command if no command is given the subsequent ticks
    REPEAT_MISSING_STEP_TICKS = 30

    # RC_SCALE will get multiplied by each input RC vector component
    # Angle is counter-clockwise from 3 o'clock position, so negate the magnitude to turn properly
    RC_SCALE = glm.vec4(0.2, 0.2, 0.1, -0.05)

    TAKEOFF_COMPLETE_ERROR_MAX = 1e-1
    ARMED_MIN_THRUST = 1e-3
    TAKEOFF_COMPLETE_STABLE_TICKS = 30

    # PID controller parameters
    STRAFE_CONTROL_PARAM = {'Kp': 0.02, 'Ki': 0.0, 'Kd': 0.0}
    LIFT_CONTROL_PARAM = {'Kp': 0.03, 'Ki': 0.0156, 'Kd': 0.0084}
    TURN_CONTROL_PARAM = {'Kp': 0.2, 'Ki': 0.0, 'Kd': 0.0}

    # Whether to arm the motors before takeoff if not ARMED before TAKEOFF command is given.
    # If False, will fail to takeoff. If True, will automatically try to arm motors, then takeoff
    AUTO_TAKEOFF_ARM = True

    @staticmethod
    def _createState(init_state: Union[SimplePhysicsStateType, dict] = None) -> SimplePhysicsStateType:
        new_state: SimplePhysicsStateType = dict()

        # Apply default state. PID default coefficients may not work,
        # so you will need to provide your own PID values in the init_state

        new_state['motor_armed'] = False
        new_state['pos'] = glm.vec3(0, 0, 0)
        new_state['angle'] = glm.vec3(0, 0, 0)
        new_state['pvel'] = glm.vec4(0, 0, 0, 1)
        new_state['avel'] = glm.vec3()
        new_state['ticks'] = 0
        new_state['_lastRC'] = None
        new_state['_tickLogs'] = {}
        new_state['thrust_vec'] = glm.vec3()
        new_state['operation'] = DroneState.LANDED
        new_state['control'] = Vec4PID(
            *(PID(sample_time=None) for _ in range(4)))

        # Apply state from argument, if given
        if init_state is not None:
            new_state.update(init_state)

        return new_state

    def reset(self, state: SimplePhysicsStateType = None) -> SimplePhysicsStateType:
        if state is None:
            state = {}
        if 'control' not in state:
            target_z = 0
            if 'pos' in state:
                target_z = state['pos'].z
            # Apply different PID parameters than default
            state.update({
                'control': Vec4PID(
                    PID(**self.STRAFE_CONTROL_PARAM,
                        sample_time=None, output_limits=(-2.0, 2.0)),
                    PID(**self.STRAFE_CONTROL_PARAM,
                        sample_time=None, output_limits=(-2.0, 2.0)),
                    PID(**self.LIFT_CONTROL_PARAM,   sample_time=None, output_limits=(0.0,
                        2.0), setpoint=target_z),  # Propellers should not spin backwards
                    PID(**self.TURN_CONTROL_PARAM,
                        sample_time=None, output_limits=(-1.0, 1.0))
                )
            })
        self._state: SimplePhysicsStateType = self._createState(state)
        return self._state

    def get_debug_data(self) -> dict:
        return {
            'motor_armed': self._state['motor_armed'],
            'pos': self._state['pos'],
            'angle': self._state['angle'],
            'absvel': self._state['pvel'].xyz,
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

    def step(self, action: StepActionType, dt: float = None) -> SimplePhysicsStateType:
        '''Update the physics engine'''
        # NOTE: If dt is None, the PID controller chooses to use real-time dt. Use fixed value dt to make it repeatable.

        self._state['ticks'] += 1

        rcvec, op, params = self.decode_action(action)

        _prev_op = self._state['operation']

        # State machine
        if op is not None:
            if op == DroneAction.TAKEOFF:
                if self._state['operation'] == DroneState.LANDED:
                    self._state['operation'] = DroneState.TAKING_OFF
                    self._state['control'].z.setpoint = params.get(
                        "altitude", 10.0)
                    self._state['_tickLogs'][DroneState.TAKING_OFF] = 0

        if self._state['operation'] == DroneState.TAKING_OFF:
            z_error = self._state['control'].z.setpoint - self._state['pos'].z
            abs_speed = glm.length(self._state['pvel'].xyz)
            # print(abs_speed)
            if abs(z_error) < self.TAKEOFF_COMPLETE_ERROR_MAX:
                self._state['_tickLogs'][DroneState.TAKING_OFF] += 1
                if self._state['_tickLogs'][DroneState.TAKING_OFF] > self.TAKEOFF_COMPLETE_STABLE_TICKS:
                    self._state['operation'] = DroneState.IN_AIR

        # Emit operation change event
        if self._state['operation'] != _prev_op:
            self.emit('operation', self._state['operation'])

        # Save last RC for later
        if rcvec is not None:
            self._state['_lastRC'] = (rcvec, self._state['ticks'])
        # If no RC, reuse previous RC input for some steps
        else:
            # TODO: Allow this behaviour to be optional
            if self._state['_lastRC'] is not None and self._state['_lastRC'][0] is not None and self._state['ticks'] < self._state['_lastRC'][1] + self.REPEAT_MISSING_STEP_TICKS:
                rcvec = self._state['_lastRC'][0]
            else:
                rcvec = StepRC(0, 0, 0, 0)

        # Which direction to move using RC
        rc_vec = glm.vec4(rcvec)
        rc_vec = glm.clamp(rc_vec, -1, 1)
        rc_vec *= self.RC_SCALE

        is_on_surface = False
        is_armed = self._state['operation'] != DroneState.LANDED
        is_accept_rc = self._state['operation'] == DroneState.IN_AIR

        # RC thrust control
        if is_accept_rc:
            self._state['control'].x.setpoint = rc_vec.x  # Target velocity
            self._state['control'].y.setpoint = rc_vec.y  # Target velocity
            # Target heading angle velocity
            self._state['control'].w.setpoint = rc_vec.w
            self._state['control'].z.setpoint += rc_vec.z  # Absolute height
            if self._state['control'].z.setpoint < 0:
                self._state['control'].z.setpoint = 0.0

        # Calculate required thrust vector based on current measured velocity and position
        new_thrust_x = self._state['control'].x(self._state['pvel'].x, dt)
        new_thrust_y = self._state['control'].y(self._state['pvel'].y, dt)
        new_thrust_z = self._state['control'].z(self._state['pos'].z, dt)
        new_thrust_a = self._state['control'].w(self._state['avel'].z, dt)
        new_thrust_z = max(
            new_thrust_z, self.ARMED_MIN_THRUST if is_armed else 0.0)
        target_thrust = glm.vec3(new_thrust_x, new_thrust_y, new_thrust_z)

        # Apply this thrust to the UAV
        self._state['thrust_vec'] = target_thrust

        # Clamp thrust at maximum physically-achievable thrust
        self._state['thrust_vec'].xy = glm.clamp(
            self._state['thrust_vec'].xy, -2.0, 2.0)
        self._state['thrust_vec'].z = glm.clamp(
            self._state['thrust_vec'].z, 0.0, 1.0)

        # Angular thrust
        self._state['avel'].z = new_thrust_a

        # 3D coordinate transformation matrix
        tfmat = glm.mat4()

        tfmat = glm.translate(tfmat, self._state['thrust_vec'])
        tfmat = glm.translate(tfmat, self.GRAVITY)
        tfmat = glm.scale(tfmat, self.AIR_RESISTANCE)

        # Update velocity vector
        self._state['pvel'] = tfmat * self._state['pvel']

        # Rotate view
        self._state['angle'] += self._state['avel']

        # Velocity vector in current facing direction
        vel_facing = glm.rotate(
            self._state['pvel'].xyz, self._state['angle'].z, glm.vec3(0, 0, 1))

        # Move position
        self._state['pos'] += vel_facing

        # Hit ground
        if self._state['pos'].z < 0.0:
            # Reset velocity to 0 and position to ground
            self._state['pos'].z = 0.0
            self._state['pvel'].z = 0.0

        return self._state


__all__ = [
    'SimpleUAVDronePhysics',
    'SimplePhysicsStateType'
]
