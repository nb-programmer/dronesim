
import os
import numpy as np

import pygame
import pygame.locals

from OpenGL import GL as gl

from dronesim.render import pygl

# Simulated drone
from dronesim import DroneSimulator, DroneState, SimRPC, SimulatedDroneHandler
from dronesim.utils import callevery

# Scene rendering
from dronesim.stream import SimulatedDroneViewStreamer
from dronesim.scene.scene_flat import FlatPathMapScene

from dronesim.simapp import SimulatorApplication

class Action:
    data_timeout = 300
    data_timer = 0
    action_set = [0,0,0,0]


# Drone simulator window launcher

def main():
    START_POSITION = (-0.9, 0, 0)

    #Init application framework (mostly for GL to initialize)
    SimulatorApplication.AppInit()
    
    #Drone simulator environment
    drone = DroneSimulator(START_POSITION)
    droneScene = FlatPathMapScene()
    droneWindow = SimulatorApplication(drone, droneScene)
    
    drone.reset()

    droneWindow.loop()
    
    SimulatorApplication.AppDel()

    droneAction = Action()

    #Takeoff immediately
    #drone.takeoff()

    #TODO: Object-oriented, and bind the methods below with it
    
    def updateMotionVecFromBind(binding):
        binding['__props']['vec'] = [
            binding['sr']['value'] - binding['sl']['value'],
            binding['fw']['value'] - binding['bw']['value'],
            binding['au']['value'] - binding['ad']['value'],
            binding['rr']['value'] - binding['rl']['value']
        ]

    def performDroneActionFromBind(action : str, drone : DroneSimulator):
        if action == 'tk':
            drone.takeoff()
        elif action == 'ld':
            drone.land()
        elif action == 'rst':
            drone.reset()
            
        #droneRenderer.render(viewport=window.get_size(), state=state)
        
if __name__ == "__main__":
    main()
