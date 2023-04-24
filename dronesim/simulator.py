
from .physics import DronePhysicsEngine, SimpleUAVDronePhysics
from .sensor import SensorBase
from .objective import ObjectiveBase

from .types import StateType, StepActionType
from typing import Optional, Dict, List, Any

# Default sensors to attach
from .sensor.motion import IMUSensor


class DroneSimulator:
    def __init__(self,
                 physics_engine: DronePhysicsEngine = None,
                 default_reset_state: Dict = None,
                 objective: ObjectiveBase = None,
                 default_sensors: bool = True,
                 **additional_sensors: SensorBase
                 ):
        self.__physics: DronePhysicsEngine = physics_engine
        self.__sensors: Dict[str, SensorBase] = {}
        self.__sensor_state = {}

        self.set_default_reset_state(default_reset_state)
        self.set_objective(objective)

        # Use `SimpleDronePhysics` by default if not provided
        if self.__physics is None:
            self.__physics = SimpleUAVDronePhysics()

        # Attach some on-board sensors if requested
        if default_sensors:
            self.add_sensor(ekf0=IMUSensor())

        self.add_sensor(**additional_sensors)

        self.__metrics = {}

        self.reset()

    def add_sensor(self, **sensor: SensorBase):
        # TODO: Maybe add some checks
        self.__sensors.update(**sensor)
        if len(sensor) > 0:
            self.update_sensor_attachment_to_self(sensor.keys())
        return self

    def update_sensor_attachment_to_self(self, sensors: List[str] = None):
        '''(Re-)attach all sensors added to the simulator by calling their 'attachTo' method'''
        if sensors is None:
            sensors = self.__sensors.keys()

        for s in sensors:
            if s not in self.__sensors:
                # TODO: Log warning
                continue
            self.__sensors.get(s).attach_to(self)

    def step(self, action: StepActionType = None, dt: float = 1e-2) -> StateType:
        '''
        Mostly a passthough to the physics engine's step(), with update to the instance (metrics, etc.)
        '''
        self.__physics.step(action, dt)
        self.__metrics['ticks'] += 1

        return self.get_state()

    def get_state(self) -> StateType:
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
            obs, fitness, done = self.__objective.get_observation(
            ), self.__objective.get_fitness(), self.__objective.get_is_done()
        return (obs, fitness, done, {'state': self.state, 'metrics': self.metrics, 'sensors': self.__sensor_state})

    def reset(self, state: Optional[Any] = None) -> StateType:
        '''Reset the physics engine to set-up the initial state'''

        if state is None and self.__default_reset_state is not None:
            state = self.__default_reset_state

        self.__physics.reset(state)
        self._update_sensors()
        self._reset_metrics()

        return self.get_state()

    def set_default_reset_state(self, state):
        self.__default_reset_state = state

    def set_objective(self, objective: ObjectiveBase):
        self.__objective = objective

    def _update_sensors(self):
        # TODO: Left to implement
        self.__sensor_state = {
            sensor_name: None for sensor_name, sensor in self.__sensors.items()}

    def _reset_metrics(self):
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

    # Physics engine API passthrough

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

    @property
    def debug_data(self):
        return self.__physics.get_debug_data()


__all__ = [
    'DroneSimulator'
]
