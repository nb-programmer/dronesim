
from dronesim import DroneSimulator
from dronesim.simapp import SimulatorApplication
from dronesim.interface import IDroneControllable
from dronesim.types import DroneAction, StepRC
from dronesim.sensor.camera import Panda3DCameraSensor

import threading
import time
from collections import namedtuple

#AI stuff
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T

TENSOR_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))
class ReplayMemory(object):
    def __init__(self, capacity):
        self.memory = deque([],maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
    

'''
I/O Requirements:
Inputs:
 - n-vector (n=number of distance rays). Value is intersection distance with path, or 0 if none
 - scalar, for use in decisions or additional input
            (junction decision for example, -1=left, 1=right, 0=stop or u-turn)
Outputs:
 - vec3 - 2-degree of movements (l/r, fw/bw) and yaw control,
            representing the q-values of each action

'''

class DQN(nn.Module):
    def __init__(self, input_distances : int):
        super().__init__()
        self.dense1 = nn.Linear(input_distances, 16)
        self.dense2 = nn.Linear(16, 32)
        self.output = nn.Linear(32, 3)
        
    def forward(self, x):
        x = x.to(TENSOR_DEVICE)
        x = self.dense1(x)
        x = self.dense2(x)
        return self.output(x)

class AIDroneControlAgent(threading.Thread, IDroneControllable):
    def __init__(self):
        super().__init__(daemon=True)

        #Environment
        self.drone = DroneSimulator()
        self.model = DQN(10)

        #Add some sensors
        self.drone.addSensor(
            down_camera_rgb = Panda3DCameraSensor("downCameraRGB", size=(320,320)),
            down_camera_depth = Panda3DCameraSensor("downCameraDepth", size=(160,160), camera_type=Panda3DCameraSensor.CAMERA_TYPE_DEPTH)
        )

        self.__state = dict()
        self.start()

    def initEnv(self, app):
        self.drone.sensors['down_camera_rgb'].attachToEnv(app.render, app.graphicsEngine, app.win)
        self.drone.sensors['down_camera_depth'].attachToEnv(app.render, app.graphicsEngine, app.win)

        #Attach camera to the UAV, point downwards facing the floor
        self.drone.sensors['down_camera_rgb'].reparentTo(app.getUAVModelNode())
        self.drone.sensors['down_camera_rgb'].setHpr(0, -90, 0)
        self.drone.sensors['down_camera_depth'].reparentTo(app.getUAVModelNode())
        self.drone.sensors['down_camera_depth'].setHpr(0, -90, 0)

    def run(self):
        self.drone.state = {"pos": 123}
        self.drone.step({'action': DroneAction.TAKEOFF})
        for _ in range(200):
            state = self.drone.step()
        for _ in range(2000):
            state = self.drone.step(StepRC(0,0.6,0,0))
            self.__update_debug_state(state)
            time.sleep(0.01)

        #observation, reward, done, info = state
        #output = self.model.forward(torch.ones(1, 10))
        #print(output)
    
    def __update_debug_state(self, state):
        observation, reward, done, info = state
        self.__state.update({
            'simulator': info['metrics'],
            'generation': 0,
            'iteration': 0,
            'training_epoch': 0,

            'reward': reward,
            'state': info['state'],
            'observation': observation,
            'sensors': len(self.drone.sensors)
        })

    def get_current_state(self):
        return self.__state

def main():
    droneControl = AIDroneControlAgent()
    droneWindow = SimulatorApplication(droneControl)
    droneControl.initEnv(droneWindow)
    droneWindow.run()

if __name__ == "__main__":
    main()
