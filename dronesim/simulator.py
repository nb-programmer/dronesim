
import typing
import numpy as np

from dronesim.physics import DronePhysicsEngine, SimpleDronePhysics
from dronesim.utils import StateType, StepAction, StepActionType

class AerialEffects:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rand_acc_xy = 0.0
        self.rand_acc_z = 0.0
        self.rand_acc_a = 0.0

    def applyShakeEffect(self, velvec : np.ndarray , max_noise_magnitude : float = 1e-1, factors : np.ndarray = None, influence_value : float = 0.0):
        #Random shaking Brownian motion
        noise_magnitude = np.random.uniform(0, max_noise_magnitude) * np.clip(influence_value * 1e-1, 0.5, 1.5)
        self.rand_acc_xy += np.random.uniform(0, 2*np.pi)
        self.rand_acc_z += np.random.uniform(0, 2*np.pi)
        self.rand_acc_a += np.random.uniform(0, 2*np.pi)
        a0 = np.cos(self.rand_acc_xy) * noise_magnitude
        a1 = np.sin(self.rand_acc_xy) * noise_magnitude
        a2 = np.sin(self.rand_acc_z) * 1.8 * noise_magnitude
        a3 = np.sin(self.rand_acc_a) * 0.01 * noise_magnitude
        print(a0, a1, a2, a3)

class EKFSensor:
    def update(self):
        pass

if __name__ == "__main__":
    np.random.seed(0)
    x = AerialEffects()
    vel = np.zeros(4)
    x.applyShakeEffect(vel)
    print(vel)
    x.applyShakeEffect(vel)
    print(vel)
    x.applyShakeEffect(vel)
    print(vel)

#TODO: Separate EKF measurements from control velocity (this was a hack)

class DroneSimulator:
    TAKEOFF_ALTITUDE = 2.0

    def __init__(self,
        start_pos : typing.Union[np.ndarray, typing.List, typing.Tuple] = (0,0,0),
        start_rot : typing.Union[np.ndarray, typing.List, typing.Tuple] = (0,0,0),
        physics_engine : DronePhysicsEngine = None,
        additional_sensors : typing.Dict[str, typing.Any] = {}
    ):
        self.init_pos = np.array(start_pos).flatten()
        self.init_rot = np.array(start_rot).flatten()
        self.init_pos.resize(3)
        self.init_rot.resize(3)

        self.__physics : DronePhysicsEngine = None
        self.__sensors = {'ekf0': None, **additional_sensors}
        self.__ext_state = {}

        self._initPhysics(physics_engine)
        self._initSensors()

        self.reset()

    def _initSensors(self):
        pass

    def _initPhysics(self, physics_engine : DronePhysicsEngine):
        if physics_engine is None:
            physics_engine = SimpleDronePhysics()
        self.__physics = physics_engine

    def step(self, action : StepActionType = None) -> StateType:
        if action is None:
            #Use default action (halt motion) if not provided
            action = StepAction(0,0,0,0)

        self.__physics.step(action)

        return self._getState()

    def _getState(self) -> StateType:
        '''
        Get the current state of the drone simulator from the objective and physics engine.

        The 'observation' parameter is the value obtained from the currently active objective (if any), or None.

        Also note that the shape of the 'state' field depends on the physics engine,
        but it is guaranteed to be of shape (2,3) minimum, which means it will at least have the
        position vector and angle vector in [[[x,y,z][x,y,z]]] format.
        
        Other data may be added by the Physics engine to further indices of the
        first axis (the '2' will be a higher number). For example, the SimpleDronePhysics engine
        uses the shape (4,3), where the last two indices contains instantaneous velocity of position and velocity.
        '''
        return (None, 0, False, {'state': self.state, 'operation': self.operation, 'ekf': self.ekf, **self.__ext_state})

    def reset(self):
        #Reset the physics engine to set-up the initial state
        self.__physics.reset(start_pos=self.init_pos, start_rot=self.init_rot)

        #Additional EKF "sensor"
        #TODO: Remove this
        self.ekf = {
            'velocity': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'rot': 0.0
            }
        }

        return self._getState()

    #Physics engine API passthrough

    @property
    def physics(self):
        return self.__physics

    @property
    def operation(self):
        return self.__physics.operation

    @property
    def state(self):
        return self.__physics.state

    def takeoff(self):
        return self.__physics.takeoff()

    def land(self):
        return self.__physics.land()


#Optional Gym environment

try:
    from gym import Env, spaces
except ImportError:
    #Stub class if gym is not installed
    class Env: pass

#TODO: Still more left to implement: Env state

class DroneSimulatorGym(DroneSimulator, Env):
    metadata = {"render_modes": ["rgb_array"]}
    def __init__(self, start_pos=(0,0,0)):
        DroneSimulator.__init__(self, start_pos)
        #TODO: Make observation space a property and get values from objective
        self.action_space = spaces.Box(-1, 1, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(np.negative(np.inf), np.inf, shape=(4,), dtype=np.float32)

    def step(self, action=None):
        return DroneSimulator.step(self, action)

    def reset(self, *, seed = None, return_info: bool = False, options = None):
        Env.reset(self, seed=seed)
        _s = DroneSimulator.reset(self)
        #Gym only returns the observation on reset, not the info unless requested
        return (_s[0], _s[3]) if return_info else _s[0]
