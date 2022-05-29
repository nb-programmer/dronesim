
import numpy as np

class DroneState:
    LANDED = 0
    TAKING_OFF = 1
    IN_AIR = 2
    LANDING = 3

#TODO: Separate EKF measurements from control velocity (this was a hack)

class SimpleDroneSimulator:
    TAKEOFF_ALTITUDE = 2.0

    def __init__(self, start_pos=(0,0,0)):
        self.init_pos = start_pos
        self.reset()

    def step(self, action=None):
        apply_wind = False
        if self.operation == DroneState.LANDED:
            self.ekf['velocity']['z'] -= 0.01
            #Friction
            self.ekf['velocity']['x'] *= 0.95
            self.ekf['velocity']['y'] *= 0.95
            self.ekf['velocity']['z'] *= 0.99
            self.ekf['velocity']['rot'] = 0.0
        elif self.operation == DroneState.TAKING_OFF:
            err = (self.TAKEOFF_ALTITUDE - self.state[2])
            self.state[2] += err * 0.009
            if abs(err) < 0.5:
                apply_wind = True
            if abs(err) < 0.02:
                self.operation = DroneState.IN_AIR
            self.ekf['velocity']['x'] = 0.0
            self.ekf['velocity']['y'] = 0.0
            self.ekf['velocity']['z'] = 0.0
        elif self.operation == DroneState.IN_AIR:
            apply_wind = True
            self.ekf['velocity']['x'] = action[0]
            self.ekf['velocity']['y'] = action[1]
            self.ekf['velocity']['z'] = action[2]
            self.ekf['velocity']['rot'] = action[3]
        elif self.operation == DroneState.LANDING:
            err = (0.0 - self.state[2])
            self.state[2] += err * 0.009
            if abs(err) < 0.5:
                apply_wind = True
            if abs(err) < 0.02:
                self.operation = DroneState.LANDED
            self.ekf['velocity']['x'] = 0.0
            self.ekf['velocity']['y'] = 0.0
            self.ekf['velocity']['z'] = 0.0
            self.ekf['velocity']['rot'] = 0.0

        #Brownian motion due to wind
        MAX_NOISE_MAG = 1e-1
        noise_magnitude = np.random.uniform(0, MAX_NOISE_MAG) * np.clip(self.state[2] * 1e-1, 0.5, 1.5)
        self.rand_acc_xy += np.random.uniform(0, 2*np.pi)
        self.rand_acc_z += np.random.uniform(0, 2*np.pi)
        self.rand_acc_a += np.random.uniform(0, 2*np.pi)

        if apply_wind:
            self.ekf['velocity']['x'] += np.cos(self.rand_acc_xy) * noise_magnitude
            self.ekf['velocity']['y'] += np.sin(self.rand_acc_xy) * noise_magnitude
            self.ekf['velocity']['z'] += np.sin(self.rand_acc_z) * 1.8 * noise_magnitude
            self.ekf['velocity']['rot'] += np.sin(self.rand_acc_a) * 0.01 * noise_magnitude

        self.ekf['velocity']['x'] = np.clip(self.ekf['velocity']['x'], -1, 1)
        self.ekf['velocity']['y'] = np.clip(self.ekf['velocity']['y'], -1, 1)
        self.ekf['velocity']['z'] = np.clip(self.ekf['velocity']['z'], -1, 1)

        c, s = np.cos(self.state[3]), np.sin(self.state[3])
        rot_mat = np.array(((c,-s),(s,c)))
        vel_vec = np.array((self.ekf['velocity']['x'], self.ekf['velocity']['y']))
        xyvec = rot_mat.dot(vel_vec)

        self.state[0] += xyvec[0] * 0.009
        self.state[1] += xyvec[1] * 0.009
        self.state[2] += self.ekf['velocity']['z'] * 0.005
        self.state[3] += -self.ekf['velocity']['rot'] * (0.009 * 2)

        if self.state[2] < 0.0:
            #Hit ground
            self.state[2] = 0.0
            self.ekf['velocity']['z'] = 0.0
        return self._getState()

    def _getState(self):
        return (self.state, 0, False, {'operation': self.operation, 'ekf': self.ekf})

    def takeoff(self):
        if self.operation == DroneState.LANDED:
            self.operation = DroneState.TAKING_OFF

    def land(self):
        if self.operation == DroneState.IN_AIR or self.operation == DroneState.TAKING_OFF:
            self.operation = DroneState.LANDING

    def reset(self):
        self.state = [*self.init_pos,0]
        self.operation = DroneState.LANDED
        self.rand_acc_xy = 0.0
        self.rand_acc_z = 0.0
        self.rand_acc_a = 0.0
        self.ekf = {
            'velocity': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'rot': 0.0
            }
        }
        return self._getState()

#Optional Gym environment

try:
    from gym import Env, spaces
except ImportError:
    #Stub class if gym is not installed
    class Env: pass

#TODO: Still more left to implement: Env state

class SimpleDroneSimulatorGym(SimpleDroneSimulator, Env):
    metadata = {"render_modes": ["rgb_array"]}
    def __init__(self, start_pos=(0,0,0)):
        SimpleDroneSimulator.__init__(self, start_pos)
        self.action_space = spaces.Box(-1, 1, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(np.negative(np.inf), np.inf, shape=(4,), dtype=np.float32)

    def step(self, action=None):
        return SimpleDroneSimulator.step(self, action)

    def reset(self, *, seed = None, return_info: bool = False, options = None):
        Env.reset(self, seed=seed)
        _s = SimpleDroneSimulator.reset(self)
        return (_s[0], _s[3]) if return_info else _s[0]
