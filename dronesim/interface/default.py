
from .control import IDroneControllable
from .action import DroneAction
from .state import DroneState
from ..types import  StepRC, StepActionType
from ..simulator import DroneSimulator

from queue import Queue, Empty
from contextlib import suppress

from typing import Optional
import threading, time

#Extends Thread, implements IDroneControllable
class DefaultDroneControl(threading.Thread, IDroneControllable):
    '''
    Allows the simulator to be controlled by the user using high-level functions in real time.

    This interface is thread-safe.
    '''
    def __init__(self,
                 drone : DroneSimulator,
                 tick_rate : float = 100,
                 auto_start : bool = True,
                 update_enable : bool = True,
                 use_physics_dt : bool = False,
                 tps_update_period : float = 1,
                 wait_till_started : bool = True):
        super().__init__(daemon=True, target=self._droneTickLoop)
        self.drone = drone
        self._tick_rate = tick_rate
        if self._tick_rate <= 0:
            self._tick_rate = 100
        self._update_enable = update_enable
        self._tps_update_period = tps_update_period
        if self._tps_update_period <= 0:
            self._tps_update_period = 1.0

        self._use_dt = use_physics_dt

        self.__debug_data = dict(tps=0)
        #Store last state
        self.__state = None
        #FIFO to process commands called using the interface methods
        self.__cmd_queue : Queue[StepActionType] = Queue()

        self._ev_started = threading.Event()
        self._predicate = threading.Condition()

        if auto_start:
            self.start()
        if wait_till_started:
            self.wait_for_start()

    def wait_for_start(self, timeout=None):
        self._ev_started.wait(timeout)

    def wait_till_done(self):
        '''Block till all actions from the command queue are performed'''
        self.__cmd_queue.join()

    def enable_update(self):
        self._update_enable = True

    def disable_update(self):
        self._update_enable = False


    def _initEventHandlers(self):
        def _notifyOperationChange(state):
            with self._predicate:
                self._predicate.notify_all()
        self.drone.physics.on('operation', _notifyOperationChange)

    def _droneTickLoop(self):
        next_time = time.time()
        last_ticks, last_tick_check = 0, time.time()

        self._initEventHandlers()

        self._ev_started.set()

        while True:
            tick_period = (1.0 / self._tick_rate)

            #Get action given
            cmd = None
            with suppress(Empty):
                cmd = self.__cmd_queue.get_nowait()
                self.__cmd_queue.task_done()

            #Perform step, even if no commands are available
            if self._update_enable:
                self.__state = self.drone.step(cmd, tick_period if self._use_dt else None)

            #Update TPS
            if time.time() - last_tick_check >= self._tps_update_period:
                tickDiff = (self.drone.metrics['ticks'] - last_ticks) / self._tps_update_period
                last_ticks = self.drone.metrics['ticks']
                self.__debug_data['tps'] = int(tickDiff)
                last_tick_check = time.time()

            #Update debug state info from the simulation step
            if self.__state is not None:
                observation, reward, done, info = self.__state
                self.__debug_data.update({
                    'state': self.drone.debug_data,
                    'observation': observation,
                    'reward': reward,
                    'sensors': len(self.drone.sensors)
                })

            #Wait for next step (keeping constant rate)
            next_time += tick_period
            delaySleep = max(0, next_time - time.time())
            time.sleep(delaySleep)


    #Implement interface functions

    def get_current_state(self):
        return self.__state

    def get_debug_data(self) -> dict:
        return self.__debug_data

    def rc_control(self, vector : StepRC):
        self.__cmd_queue.put_nowait(vector)

    def direct_action(self, action : DroneAction, **params):
        self.__cmd_queue.put_nowait({
            'action': action,
            'params': params
        })

    def takeoff(self, blocking=True, timeout=None):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.TAKEOFF
        })
        if blocking:
            with self._predicate:
                #TODO: simulator will alert if takeoff failed, raise exception here
                def _wait_takeoff():
                    return self.drone.state.get('operation') == DroneState.IN_AIR
                self._predicate.wait_for(_wait_takeoff, timeout)

    def land(self, blocking=True, timeout=None):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.LAND
        })
        if blocking:
            with self._predicate:
                #TODO: simulator will alert if landing failed, raise exception here
                def _wait_land():
                    return self.drone.state.get('operation') == DroneState.LANDED
                self._predicate.wait_for(_wait_land, timeout)

    def move_left(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def move_right(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def move_forward(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def move_backward(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def move_up(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def move_down(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def rotate_clockwise(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def rotate_counterclockwise(self, x : float, s : Optional[float] = None, blocking=True, timeout=None):
        raise NotImplementedError()

    def freeze(self, blocking=True, timeout=None):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.STOP_IN_PLACE
        })
