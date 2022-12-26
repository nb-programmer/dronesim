
from .control import IDroneControllable
from ..simulator import DroneSimulator
from ..types import DroneAction, StepRC, StepActionType

from queue import Queue, Empty

import threading, time

class DefaultDroneControl(IDroneControllable):
    '''
    Allows the drone to be controlled by the user with no automatic control
    '''
    def __init__(self,
                 drone : DroneSimulator,
                 tick_rate : float = 100,
                 update_enable : bool = False,
                 tps_update_period = 1):
        self.drone = drone
        self._tick_rate = tick_rate
        self._update_enable = update_enable
        self._tps_update_period = tps_update_period

        self.__debug_data = dict(tps=0)
        self.__state = None
        self.__cmd_queue : Queue[StepActionType] = Queue()

        self._th = threading.Thread(target=self.droneTick, daemon=True)
        self._th.start()
        
    def enableUpdate(self):
        self._update_enable = True
        
    def disableUpdate(self):
        self._update_enable = False

    def droneTick(self):
        next_time = time.time()
        last_ticks, last_tick_check = 0, time.time()

        while True:
            #Get action given
            cmd = None
            try:
                cmd = self.__cmd_queue.get_nowait()
            except Empty:
                pass

            #Perform step
            if self._update_enable:
                self.__state = self.drone.step(cmd)

            #Update TPS
            if time.time() - last_tick_check >= self._tps_update_period:
                tickDiff = (self.drone.metrics['ticks'] - last_ticks) / self._tps_update_period
                last_ticks = self.drone.metrics['ticks']
                self.__debug_data['tps'] = int(tickDiff)
                last_tick_check = time.time()
                
            #Update debug state info from the simulation step
            observation, reward, done, info = self.__state
            self.__debug_data.update({
                'state': info['state'],
                'observation': observation,
                'reward': reward,
                'sensors': len(self.drone.sensors)
            })
            
            #Wait for next step (keeping constant rate)
            next_time += (1.0 / self._tick_rate)
            delaySleep = next_time - time.time()
            time.sleep(max(0, delaySleep))

    def get_current_state(self):
        return self.__state

    def get_debug_data(self) -> dict:
        return self.__debug_data

    def rc_control(self, vector : StepRC):
        self.__cmd_queue.put_nowait(vector)

    def takeoff(self):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.TAKEOFF
        })

    def land(self):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.LAND
        })

    def freeze(self):
        self.__cmd_queue.put_nowait({
            'action': DroneAction.STOPINPLACE
        })

    def direct_action(self, action : DroneAction, args : dict = None):
        if args is None: args = {}
        self.__cmd_queue.put_nowait({
            'action': action,
            **args
        })
