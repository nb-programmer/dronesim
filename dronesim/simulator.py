
from .physics import DronePhysicsEngine, SimpleDronePhysics
from .sensor import SensorBase
from .objective import ObjectiveBase
from .types import StateType, StepActionType

#Default sensors to attach
from .sensor.motion import IMUSensor

import typing

class DroneSimulator:
    def __init__(self,
        physics_engine : DronePhysicsEngine = None,
        default_reset_state : typing.Dict = None,
        objective : ObjectiveBase = None,
        default_sensors : bool = True,
        **additional_sensors : SensorBase
    ):
        self.__physics : DronePhysicsEngine = physics_engine
        self.__sensors : typing.Dict[str, SensorBase] = {}
        self.__sensor_state = {}
        
        self.setDefaultResetState(default_reset_state)
        self.setObjective(objective)

        #Physics engine default
        if self.__physics is None:
            self.__physics = SimpleDronePhysics()
        
        #Sensor attachment
        if default_sensors:
            self.addSensor(ekf0 = IMUSensor())

        self.addSensor(**additional_sensors)

        self.__metrics = {}

        self.reset()
        
    def addSensor(self, **sensor : SensorBase):
        #TODO: Maybe add some checks
        self.__sensors.update(**sensor)
        if len(sensor) > 0:
            self.updateSensorAttachmentToSelf(sensor.keys())
        return self

    def updateSensorAttachmentToSelf(self, sensors : typing.List[str] = None):
        '''(Re-)attach all sensors added to the simulator by calling their 'attachTo' method'''
        if sensors is None:
            sensors = self.__sensors.keys()

        for s in sensors:
            if s not in self.__sensors:
                #TODO: Log warning
                continue
            self.__sensors.get(s).attachTo(self)
            
    def step(self, action : StepActionType = None) -> StateType:
        '''
        Mostly a passthough to the physics engine's step(), with update to the instance (metrics, etc.)
        '''
        self.__physics.step(action)
        self.__metrics['ticks'] += 1

        return self.getState()

    def getState(self) -> StateType:
        '''
        Get the current state of the drone simulator from the objective and physics engine, according to the Gym specifications:
            (observation, reward, done, info)

        The 'observation' and 'reward' parameters are the values obtained from the currently active objective (if any), or None and 0.

        In the 'info' part, the 'state' field depends on the physics engine, and can define its own properties.
        You can expect it to contain at least 'pos' field with a 3-D vector of some sorts.

        Other fields in info may include state of various sensors attached and the 'metrics' for simulation stats
        
        '''
        obs, fitness, done = None, None, False
        if self.__objective is not None:
            obs, fitness, done = self.__objective.getObservation(), self.__objective.getFitness(), self.__objective.getIsDone()
        return (obs, fitness, done, {'state': self.state, 'metrics': self.metrics, 'sensors': self.__sensor_state})

    def reset(self, state = None):
        #Reset the physics engine to set-up the initial state

        if state is None and self.__default_reset_state is not None:
            state = self.__default_reset_state

        self.__physics.reset(state)
        self._updateSensors()
        self._resetMetrics()

        return self.getState()

    def setDefaultResetState(self, state):
        self.__default_reset_state = state

    def setObjective(self, objective : ObjectiveBase):
        self.__objective = objective

    def _updateSensors(self):
        #TODO: Left to implement
        self.__sensor_state = {sensor_name : None for sensor_name, sensor in self.__sensors.items()}

    def _resetMetrics(self):
        '''Reset default metric values'''
        self.__metrics.update({
            'ticks': 0
        })

    @property
    def metrics(self):
        return self.__metrics

    @property
    def sensors(self):
        return self.__sensors

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
    @state.setter
    def state(self, state):
        self.__physics.state = state


#Optional Gym environment

try:
    from gym import Env, spaces
except ImportError:
    #Stub class if gym is not installed
    class Env: pass

#TODO: Still more left to implement: Env state

class DroneSimulatorGym(DroneSimulator, Env):
    metadata = {"render_modes": ["rgb_array"]}
    def __init__(self, *args, **kwargs):
        DroneSimulator.__init__(self, *args, **kwargs)
        #TODO: Make observation space a property and get values from objective
        #self.action_space = spaces.Box(-1, 1, shape=(4,), dtype=np.float32)
        #self.observation_space = spaces.Box(np.negative(np.inf), np.inf, shape=(4,), dtype=np.float32)

    def step(self, action=None):
        return DroneSimulator.step(self, action)

    def reset(self, *, seed = None, return_info: bool = False, options = None):
        Env.reset(self, seed=seed)
        _s = DroneSimulator.reset(self)
        #Gym only returns the observation on reset, not the info unless requested
        return (_s[0], _s[3]) if return_info else _s[0]
