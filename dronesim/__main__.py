
#Simulated drone
from dronesim import DroneSimulator
from dronesim.interface import DefaultDroneControl

#Sensors
from dronesim.sensor.panda3d.camera import Panda3DCameraSensor

#App window
from dronesim.simapp import SimulatorApplication

import argparse

def main():
    parser = argparse.ArgumentParser()
    #TODO: Having some options would be nice
    parser.parse_args()

    #Simulator environment
    drone = DroneSimulator()
    droneControl = DefaultDroneControl(drone, update_enable=True)
    #Application
    droneWindow = SimulatorApplication(droneControl)
    #== Add a camera sensor facing down ==
    downCam = Panda3DCameraSensor("downCameraRGB", size=(320,320))
    drone.addSensor(down_camera_rgb = downCam)
    #Insert camera into main app window and attach to the scene
    downCam.attachToEnv(droneWindow.render, droneWindow.graphicsEngine, droneWindow.win)
    #Move and rotate camera with the UAV object
    downCam.reparentTo(droneWindow.getUAVModelNode())
    #Face down
    downCam.setHpr(0, -90, 0)
    #Start the app
    droneWindow.run()

if __name__ == "__main__":
    main()
